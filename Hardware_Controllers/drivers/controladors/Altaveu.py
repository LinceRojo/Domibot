import os
import subprocess
import time
import sounddevice as sd # Per llistar dispositius
from typing import Optional, List, Dict, Any

class Altaveu:
    """
    Controla la reproducció d'àudio utilitzant la comanda `aplay` en sistemes Linux (Raspberry Pi).
    Permet llistar dispositius de sortida i reproduir fitxers d'àudio.
    Implementa el protocol de gestió de context per a un control segur dels processos de reproducció.
    """
    def __init__(self, nom_altaveu: str = "AltaveuSim", 
                 device_label_alsa: Optional[str] = None):
        """
        Inicialitza l'altaveu.

        Args:
            nom_altaveu (str): Nom identificatiu.
            device_label_alsa (Optional[str]): Etiqueta ALSA per a `aplay` (ex: "default", "hw:0,0").
                                                None per utilitzar el dispositiu per defecte del sistema.
        """
        self.nom = nom_altaveu
        self._device_label_alsa = device_label_alsa
        self._playback_process: Optional[subprocess.Popen] = None # Procés de reproducció en background

        print(f"[{self.nom}]: Altaveu inicialitzat. Dispositiu ALSA: '{self._device_label_alsa if self._device_label_alsa else 'Sistema per defecte'}'.")
        print(f"[{self.nom}]: Utilitzeu 'with Altaveu(...) as spk:' per operar de forma segura.")

    def __enter__(self):
        """
        Mètode que es crida quan s'entra al bloc 'with'.
        """
        print(f"[{self.nom}]: Entrant al context.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Mètode que es crida quan se surt del bloc 'with'.
        Atura qualsevol reproducció en curs.
        """
        print(f"[{self.nom}]: Sortint del context. Aturant reproducció en curs (si n'hi ha)...")
        self._stop_playback_process() # Mètode privat per aturar el procés

    def __del__(self):
        """
        Mètode finalitzador. S'assegura que qualsevol reproducció en curs s'aturi
        si l'objecte és destruït sense passar pel context.
        """
        if self._playback_process and self._playback_process.poll() is None:
            print(f"[{self.nom}]: Executant __del__ (aturant reproducció com a salvaguarda).")
            self._stop_playback_process()

    def _stop_playback_process(self):
        """
        Atura el procés de reproducció d'àudio si n'hi ha un en marxa.
        """
        if self._playback_process and self._playback_process.poll() is None:
            print(f"[{self.nom}]: Aturant procés de reproducció (PID: {self._playback_process.pid})...")
            self._playback_process.terminate()
            try:
                self._playback_process.wait(timeout=1) # Espera un moment perquè el procés acabi
            except subprocess.TimeoutExpired:
                self._playback_process.kill() # Si no respon, el mata
            self._playback_process = None
            print(f"[{self.nom}]: Procés de reproducció aturat.")

    def list_output_devices(self, tool: str = "sounddevice") -> List[Dict[str, Any]]:
        """
        Llista els dispositius de sortida d'àudio disponibles.
        Args:
            tool (str): Eina a utilitzar per llistar ("sounddevice" o "aplay").
        Returns:
            List[Dict[str, Any]]: Llista de diccionaris amb informació dels dispositius.
        """
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
                # 'aplay -L' llista els noms de les targetes i dispositius ALSA
                result = subprocess.run(["aplay", "-L"], capture_output=True, text=True, check=True, encoding='utf-8')
                print(f"--- Sortida de 'aplay -L' ---\n{result.stdout.strip()}\n-----------------------------")
                # Per a una implementació completa, s'hauria de parsejar result.stdout
                # per extreure els noms de dispositius ALSA i afegir-los a output_devices_info.
                # Per simplicitat, ara només la imprimeix.
            except (FileNotFoundError, subprocess.CalledProcessError) as e: 
                print(f"[{self.nom} ERROR]: Error llistant amb 'aplay -L': {e}. Assegura't que 'alsa-utils' està instal·lat.")
        else: 
            print(f"[{self.nom} ERROR]: Eina '{tool}' no reconeguda. Utilitza 'sounddevice' o 'aplay'.")
        
        return output_devices_info

    def play_audio_file(self, filepath: str, blocking: bool = True) -> bool:
        """
        Reprodueix un fitxer d'àudio utilitzant la comanda 'aplay'.
        Args:
            filepath (str): La ruta completa al fitxer d'àudio (ex: .wav).
            blocking (bool): Si True, la funció espera que la reproducció acabi.
                             Si False, la reproducció es fa en background.
        Returns:
            bool: True si la reproducció s'inicia amb èxit, False altrament.
        """
        if not os.path.exists(filepath):
            print(f"[{self.nom} ERROR]: El fitxer d'àudio '{filepath}' no existeix.")
            return False
        
        # Comprovar si 'aplay' està disponible
        try:
            subprocess.run(["aplay", "--version"], capture_output=True, check=True, timeout=1)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"[{self.nom} ERROR]: 'aplay' no trobat o no funcional. Instal·la 'alsa-utils' (sudo apt install alsa-utils).")
            return False

        aplay_command = ["aplay"]
        if self._device_label_alsa:
            aplay_command.extend(["-D", self._device_label_alsa]) # Especifica el dispositiu ALSA
        aplay_command.append(filepath)

        print(f"[{self.nom}]: Comanda de reproducció: {' '.join(aplay_command)}")

        if self._playback_process and self._playback_process.poll() is None:
            print(f"[{self.nom} WARNING]: Ja hi ha una reproducció en curs. Aturant l'anterior per iniciar la nova.")
            self._stop_playback_process() # Aturem l'anterior abans d'iniciar una de nova

        try:
            if blocking:
                result = subprocess.run(aplay_command, capture_output=True, text=True, check=False, encoding='utf-8')
                if result.returncode == 0:
                    print(f"[{self.nom}]: Reproducció de '{os.path.basename(filepath)}' finalitzada.")
                    return True
                else:
                    print(f"[{self.nom} ERROR `aplay`]: La reproducció de '{os.path.basename(filepath)}' ha fallat. Error: {result.stderr.strip()}")
                    return False
            else: # Non-blocking (en background)
                self._playback_process = subprocess.Popen(aplay_command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                print(f"[{self.nom}]: Reproducció iniciada en background (PID: {self._playback_process.pid}).")
                
                # Comprovació ràpida si el procés ha fallat immediatament
                time.sleep(0.1) # Donem un petit temps al procés per iniciar-se o fallar
                if self._playback_process.poll() is not None: # Si el procés ja ha acabat
                    _, stderr = self._playback_process.communicate()
                    print(f"[{self.nom} ERROR `aplay` background]: La reproducció en background ha fallat. Error: {stderr.decode(errors='ignore').strip()}")
                    self._playback_process = None # Resetejem el procés
                    return False
                return True
        except Exception as e:
            print(f"[{self.nom} ERROR execució `aplay`]: Error inesperat durant l'execució d'aplay: {e}")
            if self._playback_process: # Assegurem que el procés es neteja si hi ha un error inesperat
                self._stop_playback_process()
            return False
