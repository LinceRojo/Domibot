import os
import subprocess
import time
import sounddevice as sd
from typing import Optional, List, Dict, Any

# IMPORTS ADDICIONALS PER AL TPA2016
import busio
import board
import adafruit_tpa2016

class Altaveu:
    """
    Controla la reproducció d'àudio utilitzant la comanda `aplay` en sistemes Linux (Raspberry Pi).
    Permet llistar dispositius de sortida i reproduir fitxers d'àudio.
    Integra el control de l'amplificador Adafruit TPA2016 via I2C per ajustar el guany.
    Implementa el protocol de gestió de context per a un control segur.
    """
    def __init__(self, nom_altaveu: str = "AltaveuSim",
                 device_label_alsa: Optional[str] = None,
                 initial_tpa_gain_db: float = 0.0, # Nou: Guany inicial per al TPA2016 (en dB)
                 tpa_i2c_address: int = 0x58 # Adreça I2C per defecte del TPA2016
                ):
        self.nom = nom_altaveu
        self._device_label_alsa = device_label_alsa
        self._playback_process: Optional[subprocess.Popen] = None

        # Propietats per al TPA2016
        self._tpa2016_amp: Optional[adafruit_tpa2016.TPA2016] = None
        self._initial_tpa_gain_db = initial_tpa_gain_db
        self._tpa_i2c_address = tpa_i2c_address

        print(f"[{self.nom}]: Altaveu inicialitzat. Dispositiu ALSA: '{self._device_label_alsa if self._device_label_alsa else 'Sistema per defecte'}'.")
        print(f"[{self.nom}]: Guany inicial TPA2016 configurat a: {self._initial_tpa_gain_db} dB.")
        print(f"[{self.nom}]: Utilitzeu 'with Altaveu(...) as spk:' per operar de forma segura.")

    def __enter__(self):
        """
        Mètode que es crida quan s'entra al bloc 'with'.
        Inicialitza i configura el TPA2016 aquí.
        """
        print(f"[{self.nom}]: Entrant al context.")
        try:
            # Inicialitzar I2C (si encara no s'ha fet globalment per CircuitPython)
            # Aquesta part depèn de com es gestiona `busio.I2C` a nivell de projecte.
            # Per simplicitat i si és l'únic I2C, ho fem aquí.
            # S'hauria de capturar l'excepció si els pins I2C no estan disponibles o no estan configurats
            i2c = busio.I2C(board.SCL, board.SDA)
            self._tpa2016_amp = adafruit_tpa2016.TPA2016(i2c, address=self._tpa_i2c_address)

            # Configuració del TPA2016
            self._tpa2016_amp.amplifier_shutdown = False # Assegurar que l'amp estigui actiu
            self._tpa2016_amp.speaker_enable_l = True
            self._tpa2016_amp.speaker_enable_r = True
            
            # Ajustar el guany inicial
            self._tpa2016_amp.fixed_gain = self._initial_tpa_gain_db
            print(f"[{self.nom}]: TPA2016 detectat i configurat. Guany establert a {self._tpa2016_amp.fixed_gain} dB.")

            # Opcional: Configuració addicional de l'AGC si no es vol el comportament per defecte
            # Per exemple, per deshabilitar l'AGC per complet (guany purament fix):
            # self._tpa2016_amp.compression_ratio = adafruit_tpa2016.AGC_OFF
            # print(f"[{self.nom}]: AGC del TPA2016 deshabilitat.")

        except ValueError as e:
            print(f"[{self.nom} ERROR TPA2016]: No s'ha pogut inicialitzar I2C o el TPA2016: {e}. Revisa pins I2C i configuració (raspi-config).")
            self._tpa2016_amp = None # Assegurar que no hi hagi un objecte TPA invàlid
        except RuntimeError as e:
            print(f"[{self.nom} ERROR TPA2016]: No s'ha trobat el TPA2016 a l'adreça I2C {hex(self._tpa_i2c_address)}: {e}. Revisa les connexions.")
            self._tpa2016_amp = None
        except Exception as e:
            print(f"[{self.nom} ERROR TPA2016 inesperat]: Error durant la configuració del TPA2016: {e}")
            self._tpa2016_amp = None
            
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Mètode que es crida quan se surt del bloc 'with'.
        Atura qualsevol reproducció en curs i posa el TPA2016 en mode shutdown.
        """
        print(f"[{self.nom}]: Sortint del context. Aturant reproducció en curs (si n'hi ha)...")
        self._stop_playback_process() # Mètode privat per aturar el procés

        # Neteja i apagat del TPA2016
        if self._tpa2016_amp:
            try:
                self._tpa2016_amp.amplifier_shutdown = True # Apaga l'amplificador
                print(f"[{self.nom}]: TPA2016 posat en mode shutdown.")
            except Exception as e:
                print(f"[{self.nom} ERROR TPA2016]: Error en apagar el TPA2016: {e}")

        if exc_type: # Si hi ha hagut una excepció en el bloc 'with'
            print(f"[{self.nom} ERROR]: S'ha produït una excepció en el context: {exc_val}")

    def __del__(self):
        """
        Mètode finalitzador. S'assegura que qualsevol reproducció en curs s'aturi
        si l'objecte és destruït sense passar pel context.
        ADVERTIMENT: No és segur dependre del TPA2016 en __del__ ja que els recursos I2C
        poden ja no estar disponibles quan es crida aquest mètode.
        Per això, l'apagat principal es fa a __exit__.
        """
        if self._playback_process and self._playback_process.poll() is None:
            print(f"[{self.nom}]: Executant __del__ (aturant reproducció com a salvaguarda).")
            self._stop_playback_process()
        # No intentem apagar el TPA2016 aquí, ja que els recursos I2C poden haver-se alliberat
        # La neteja del TPA2016 es fa principalment a __exit__

    def _stop_playback_process(self):
        """
        Atura el procés de reproducció d'àudio si n'hi ha un en marxa.
        """
        if self._playback_process and self._playback_process.poll() is None:
            print(f"[{self.nom}]: Aturant procés de reproducció (PID: {self._playback_process.pid})...")
            self._playback_process.terminate()
            try:
                self._playback_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._playback_process.kill()
            self._playback_process = None
            print(f"[{self.nom}]: Procés de reproducció aturat.")

    def list_output_devices(self, tool: str = "sounddevice") -> List[Dict[str, Any]]:
        # ... (Aquest mètode es manté igual)
        output_devices_info = []
        print(f"\n[{self.nom}] Dispositius de sortida disponibles (amb {tool}):")

        if tool == "sounddevice":
            try:
                devices = sd.query_devices()
                found_any = False
                for i, dev in enumerate(devices):
                    if dev.get('max_output_channels', 0) > 0: # Només dispositius de sortida
                        device_info = {
                            "index_sd": i,
                            "name": dev.get('name', 'N/A'),
                            "max_output_channels": dev.get('max_output_channels', 0),
                            "hostapi_name": sd.query_hostapis(dev.get('hostapi', -1))['name'] if dev.get('hostapi', -1) != -1 else 'N/A'
                        }
                        print(f"  Índex SD {i}: {device_info['name']} (API: {device_info['hostapi_name']})")
                        output_devices_info.append(device_info)
                        found_any = True
                if not found_any:
                    print(f"[{self.nom} WARNING]: No s'han trobat dispositius de sortida amb sounddevice.")
            except Exception as e:
                print(f"[{self.nom} ERROR]: No s'ha pogut consultar dispositius amb sounddevice: {e}")

        elif tool == "aplay":
            try:
                result = subprocess.run(["aplay", "-L"], capture_output=True, text=True, check=True, encoding='utf-8')
                print(f"--- Sortida de 'aplay -L' ---\n{result.stdout.strip()}\n-----------------------------")
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"[{self.nom} ERROR]: Error llistant amb 'aplay -L': {e}. Assegura't que 'alsa-utils' està instal·lat.")
        else:
            print(f"[{self.nom} ERROR]: Eina '{tool}' no reconeguda. Utilitza 'sounddevice' o 'aplay'.")

        return output_devices_info

    def play_audio_file(self, filepath: str, blocking: bool = True) -> bool:
        # ... (Aquest mètode es manté gairebé igual, però ara el TPA2016 ja haurà ajustat el guany)
        if not os.path.exists(filepath):
            print(f"[{self.nom} ERROR]: El fitxer d'àudio '{filepath}' no existeix.")
            return False

        try:
            subprocess.run(["aplay", "--version"], capture_output=True, check=True, timeout=1)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"[{self.nom} ERROR]: 'aplay' no trobat o no funcional. Instal·la 'alsa-utils' (sudo apt install alsa-utils).")
            return False

        aplay_command = ["aplay"]
        if self._device_label_alsa:
            aplay_command.extend(["-D", self._device_label_alsa])
        aplay_command.append(filepath)

        print(f"[{self.nom}]: Comanda de reproducció: {' '.join(aplay_command)}")

        if self._playback_process and self._playback_process.poll() is None:
            print(f"[{self.nom} WARNING]: Ja hi ha una reproducció en curs. Aturant l'anterior per iniciar la nova.")
            self._stop_playback_process()

        try:
            if blocking:
                result = subprocess.run(aplay_command, capture_output=True, text=True, check=False, encoding='utf-8')
                if result.returncode == 0:
                    print(f"[{self.nom}]: Reproducció de '{os.path.basename(filepath)}' finalitzada.")
                    return True
                else:
                    print(f"[{self.nom} ERROR `aplay`]: La reproducció de '{os.path.basename(filepath)}' ha fallat. Error: {result.stderr.strip()}")
                    return False
            else:
                self._playback_process = subprocess.Popen(aplay_command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                print(f"[{self.nom}]: Reproducció iniciada en background (PID: {self._playback_process.pid}).")
                time.sleep(0.1)
                if self._playback_process.poll() is not None:
                    _, stderr = self._playback_process.communicate()
                    print(f"[{self.nom} ERROR `aplay` background]: La reproducció en background ha fallat. Error: {stderr.decode(errors='ignore').strip()}")
                    self._playback_process = None
                    return False
                return True
        except Exception as e:
            print(f"[{self.nom} ERROR execució `aplay`]: Error inesperat durant l'execució d'aplay: {e}")
            if self._playback_process:
                self._stop_playback_process()
            return False

    # NOU: Mètodes per controlar el TPA2016 externament (opcional però útil)
    def set_tpa_gain(self, gain_db: float) -> None:
        """
        Ajusta el guany de l'amplificador TPA2016 en dB.
        Args:
            gain_db (float): Guany desitjat en dB (-28 a 30).
        """
        if self._tpa2016_amp:
            try:
                # El xip pot tenir un rang limitat de guany segons l'AGC.
                # Per defecte, fixed_gain és de -28 a 30dB.
                self._tpa2016_amp.fixed_gain = gain_db
                print(f"[{self.nom}]: Guany del TPA2016 ajustat a {self._tpa2016_amp.fixed_gain} dB.")
            except ValueError as e:
                print(f"[{self.nom} ERROR TPA2016]: Valor de guany {gain_db} fora de rang o invàlid: {e}")
            except Exception as e:
                print(f"[{self.nom} ERROR TPA2016]: Error en ajustar el guany: {e}")
        else:
            print(f"[{self.nom} WARNING]: TPA2016 no inicialitzat. No es pot ajustar el guany.")

    def set_tpa_agc_compression(self, compression_ratio: int) -> None:
        """
        Ajusta la ràtio de compressió de l'AGC del TPA2016.
        Args:
            compression_ratio (int): Valor de compressió (p.ex., adafruit_tpa2016.AGC_OFF, TPA2016_AGC_2, etc.).
        """
        if self._tpa2016_amp:
            try:
                self._tpa2016_amp.compression_ratio = compression_ratio
                ratio_map = {
                    adafruit_tpa2016.AGC_OFF: "OFF (1:1)",
                    adafruit_tpa2016.AGC_2: "1:2",
                    adafruit_tpa2016.AGC_4: "1:4",
                    adafruit_tpa2016.AGC_8: "1:8"
                }
                print(f"[{self.nom}]: Ràtio de compressió AGC TPA2016 ajustada a {ratio_map.get(compression_ratio, 'Desconegut')}.")
            except ValueError as e:
                print(f"[{self.nom} ERROR TPA2016]: Valor de compressió invàlid: {e}")
            except Exception as e:
                print(f"[{self.nom} ERROR TPA2016]: Error en ajustar la compressió AGC: {e}")
        else:
            print(f"[{self.nom} WARNING]: TPA2016 no inicialitzat. No es pot ajustar la compressió AGC.")

    def get_tpa_current_gain(self) -> Optional[float]:
        """
        Retorna el guany actual de l'amplificador TPA2016 en dB.
        """
        if self._tpa2016_amp:
            return self._tpa2016_amp.fixed_gain
        return None
