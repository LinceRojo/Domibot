import os
import time
import numpy as np
import sounddevice as sd
from typing import Optional, Tuple, List, Dict, Any

class Microphone:
    """
    Gestiona la captura d'àudio.
    Retorna dades d'àudio, samplerate, extensió per defecte i metadades.
    """
    def __init__(self,
                 nom_microfon: str = "MicSim",
                 device_index: Optional[int] = None,
                 samplerate: int = 44100,
                 channels: int = 1,
                 dtype_gravacio: str = 'int16', # dtype per a sounddevice.rec
                 default_extension: str = "wav",
                 default_metadata: Optional[Dict[str, Any]] = None):

        self.nom = nom_microfon
        self._device_index = device_index
        self._samplerate = samplerate
        self._channels = channels
        self._dtype_gravacio = dtype_gravacio

        self._default_extension = default_extension.lower().lstrip(".")
        self._default_metadata = default_metadata if default_metadata is not None else {}

        self._is_recording_active = False
        self._stream: Optional[sd.InputStream] = None # Per a streaming asíncron

        # Validacions inicials
        if not isinstance(samplerate, int) or samplerate <= 0:
            raise ValueError(f"[{self.nom} ERROR]: La freqüència de mostreig (samplerate) ha de ser un enter positiu.")
        if not isinstance(channels, int) or channels <= 0:
            raise ValueError(f"[{self.nom} ERROR]: El nombre de canals (channels) ha de ser un enter positiu.")

        print(f"[{self.nom}]: Micròfon inicialitzat. SR={self._samplerate}, Canals={self._channels}, Extensió='{self._default_extension}'.")
        print(f"[{self.nom}]: Utilitzeu 'with Microphone(...) as mic:' per operar.")
        
        # Validar device_index si s'ha proporcionat
        if self._device_index is not None:
            print(f"[{self.nom}]: Comprovant l'índex de dispositiu: {self._device_index}")
            try:
                device_info = sd.query_devices(self._device_index)
                if device_info.get('max_input_channels', 0) == 0:
                    print(f"[{self.nom} WARNING]: L'índex {self._device_index} sembla no tenir canals d'entrada o no és un dispositiu d'entrada vàlid.")
            except sd.PortAudioError:
                print(f"[{self.nom} ERROR]: L'índex de dispositiu {self._device_index} no és vàlid o no s'ha trobat. Configuració de dispositiu automàtica (None).")
                self._device_index = None # Resetejar si és invàlid
            except Exception as e:
                print(f"[{self.nom} ERROR]: Error en verificar l'índex del dispositiu {self._device_index}: {e}. Configuració de dispositiu automàtica (None).")
                self._device_index = None

    def __enter__(self):
        print(f"[{self.nom}]: Entrant al context. Micròfon preparat.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"[{self.nom}]: Sortint del context.")
        if self._is_recording_active:
            sd.stop()
            self._is_recording_active = False
            print(f"[{self.nom} WARNING]: Gravació síncrona aturada en sortir del context.")
        if self._stream and self._stream.active:
            self.stop_streaming()
            print(f"[{self.nom} WARNING]: Streaming aturat en sortir del context.")
        if exc_type: # Si hi ha hagut una excepció
            print(f"[{self.nom} ERROR]: S'ha produït una excepció en el context: {exc_val}")


    def list_input_devices(self) -> List[Dict[str, Any]]:
        print(f"\n[{self.nom}] Dispositius d'entrada d'àudio disponibles:")
        try:
            devices = sd.query_devices()
        except Exception as e:
            print(f"[{self.nom} ERROR]: No s'ha pogut consultar els dispositius de sounddevice: {e}")
            return []
            
        input_devices_info = []
        found_any = False
        for i, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0:
                device_info = {
                    "index": i, "name": dev.get('name', 'N/A'),
                    "max_input_channels": dev.get('max_input_channels', 0),
                    "default_samplerate": dev.get('default_samplerate', 'N/A')
                }
                print(f"  Índex {i}: {device_info['name']} (Canals In: {device_info['max_input_channels']}, SR Def: {device_info['default_samplerate']})")
                input_devices_info.append(device_info)
                found_any = True
        if not found_any: print(f"[{self.nom} WARNING]: No s'han trobat dispositius d'entrada.")
        return input_devices_info

    def set_device_by_name(self, name: str) -> bool:
        """
        Intenta configurar el micròfon utilitzant el nom del dispositiu.
        Retorna True si s'ha trobat i configurat, False altrament.
        """
        print(f"[{self.nom}]: Intentant configurar el dispositiu per nom: '{name}'...")
        devices = self.list_input_devices()
        for dev in devices:
            if dev['name'].lower() == name.lower(): # Comparació sense distinció de majúscules/minúscules
                self._device_index = dev['index']
                print(f"[{self.nom}]: Dispositiu '{name}' trobat. Índex configurat a {self._device_index}.")
                return True
        print(f"[{self.nom} WARNING]: Dispositiu d'entrada amb nom '{name}' no trobat.")
        return False

    def record_audio_data(self, duration: int = 5) -> Optional[Tuple[np.ndarray, int, str, Dict[str, Any]]]:
        """
        Grava àudio de forma síncrona durant una durada específica.
        Bloqueja l'execució fins que la gravació finalitzi.
        """
        if self._is_recording_active:
            print(f"[{self.nom} ERROR]: Ja s'està fent una gravació síncrona. No es pot iniciar una de nova.")
            return None
        if self._stream and self._stream.active:
            print(f"[{self.nom} ERROR]: El mode de streaming ja està actiu. Atura'l amb '.stop_streaming()' abans de fer una gravació síncrona.")
            return None

        print(f"[{self.nom}]: Iniciant gravació síncrona ({duration} segons)...")
        try:
            self._is_recording_active = True
            audio_data = sd.rec(
                frames=int(duration * self._samplerate),
                samplerate=self._samplerate,
                channels=self._channels,
                dtype=self._dtype_gravacio,
                device=self._device_index
            )
            sd.wait() # Espera que la gravació finalitzi
            self._is_recording_active = False
            print(f"[{self.nom}]: Gravació finalitzada. Dades: {audio_data.shape}")
            return audio_data, self._samplerate, self._default_extension, self._default_metadata.copy()
        except sd.PortAudioError as e:
            self._is_recording_active = False
            print(f"[{self.nom} ERROR PortAudio]: {e}. Verifica el dispositiu seleccionat (índex {self._device_index}) o si el micròfon està connectat correctament.")
        except sd.SoundDeviceError as e:
            self._is_recording_active = False
            print(f"[{self.nom} ERROR SoundDevice]: {e}. Comprova la configuració de samplerate/canals ({self._samplerate}Hz, {self._channels}ch) o si el dispositiu està disponible i no en ús.")
        except Exception as e:
            self._is_recording_active = False
            print(f"[{self.nom} ERROR inesperat]: S'ha produït un error durant la gravació: {e}")
            
        return None

    def start_streaming(self, callback_function: callable, blocksize: int = 1024):
        """
        Inicia la gravació d'àudio en mode streaming.
        La funció 'callback_function(indata, frames, time, status)' serà cridada per cada bloc d'àudio.
        'blocksize' determina la mida dels blocs (en mostres).
        """
        if self._is_recording_active:
            print(f"[{self.nom} ERROR]: Ja s'està fent una gravació síncrona. Atura-la amb '.stop()' abans d'iniciar el streaming.")
            return
        if self._stream and self._stream.active:
            print(f"[{self.nom} WARNING]: El streaming ja està actiu.")
            return

        print(f"[{self.nom}]: Iniciant streaming d'àudio amb blocksize={blocksize}...")
        try:
            self._stream = sd.InputStream(
                samplerate=self._samplerate,
                channels=self._channels,
                dtype=self._dtype_gravacio,
                device=self._device_index,
                callback=callback_function,
                blocksize=blocksize # Mida del bloc de dades a processar
            )
            self._stream.start()
            print(f"[{self.nom}]: Streaming iniciat. Ara pots processar els blocs d'àudio amb la funció de callback.")
        except sd.PortAudioError as e:
            print(f"[{self.nom} ERROR PortAudio a streaming]: {e}. Verifica el dispositiu d'entrada (índex {self._device_index}).")
            self._stream = None
        except sd.SoundDeviceError as e:
            print(f"[{self.nom} ERROR SoundDevice a streaming]: {e}. Comprova la configuració de samplerate/canals ({self._samplerate}Hz, {self._channels}ch) o si el dispositiu és accessible.")
            self._stream = None
        except Exception as e:
            print(f"[{self.nom} ERROR inesperat a streaming]: S'ha produït un error a l'iniciar el streaming: {e}")
            self._stream = None

    def stop_streaming(self):
        """
        Atura la gravació d'àudio en mode streaming.
        """
        if self._stream and self._stream.active:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            print(f"[{self.nom}]: Streaming d'àudio aturat.")
        else:
            print(f"[{self.nom} WARNING]: No hi ha cap streaming d'àudio actiu per aturar.")

