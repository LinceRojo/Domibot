import os
import time
import numpy as np
from typing import Optional, Tuple, Dict, Any

# Descomentar per a ús real en Raspberry Pi amb Picamera2
#try:
from picamera2 import Picamera2 # , Preview
_PICAMERA2_AVAILABLE = True
#except ImportError:
#    print("[Camera WARNING]: Picamera2 no trobada. La càmera operarà en mode SIMULAT.")
#    _PICAMERA2_AVAILABLE = False

class Camera:
    """
    Gestiona la captura d'imatges des d'una càmera Raspberry Pi (Picamera2)
    o simula la captura si Picamera2 no està disponible.
    Implementa el protocol de gestió de context per a una inicialització i tancament segurs.
    """
    def __init__(self, nom_camera: str = "RPi Cam",
                 default_extension: str = "jpg",
                 default_metadata: Optional[Dict[str, Any]] = None,
                 resolucio: Tuple[int, int] = (1280, 720),
                 mode_preview: bool = False):
        """
        Inicialitza la càmera. La configuració i l'inici de la càmera real
        es realitzen mitjançant __enter__.

        Args:
            nom_camera (str): Nom identificatiu per a la càmera.
            default_extension (str): Extensió per defecte per a les imatges capturades (ex: "jpg", "png").
            default_metadata (Optional[Dict[str, Any]]): Metadades per defecte a associar amb cada captura.
            resolucio (Tuple[int, int]): Resolució de la imatge (amplada, alçada).
            mode_preview (bool): Si True, configura per a previsualització (més ràpid, menys detall).
                                 Si False, per a captures fixes (més lent, més detall).
        """
        self.nom = nom_camera
        self._picam2_instance: Optional[Picamera2] = None # Renombre a _picam2_instance per claredat
        self._camera_is_active = False # Indica si la càmera (real o simulada) està iniciada
        self._is_real_camera_simulated = not _PICAMERA2_AVAILABLE # True si estem en mode simulació

        self._default_extension = default_extension.lower().lstrip(".")
        self._default_metadata = default_metadata if default_metadata is not None else {}
        self._resolucio = resolucio
        self._mode_preview = mode_preview
        
        print(f"[{self.nom}]: Càmera inicialitzada. Extensió per defecte: '{self._default_extension}'.")
        print(f"[{self.nom}]: Mode: {'SIMULAT' if self._is_real_camera_simulated else 'REAL'}.")
        print(f"[{self.nom}]: Utilitzeu 'with Camera(...) as cam:' per operar de forma segura.")

    def __enter__(self):
        """
        Mètode que es crida quan s'entra al bloc 'with'.
        Configura i inicia la càmera (real o simulada).
        """
        print(f"[{self.nom}]: Entrant al context. Intentant iniciar la càmera...")
        if not self._camera_is_active:
            if not self._is_real_camera_simulated:
                try:
                    self._picam2_instance = Picamera2()
                    # Configuració per a captura fixa (BGR888 és bo per a NumPy i PIL)
                    config = self._picam2_instance.create_still_configuration(
                        main={"size": self._resolucio, "format": "BGR888"}
                    )
                    self._picam2_instance.configure(config)
                    self._picam2_instance.start()
                    time.sleep(1) # Temps per a la inicialització
                    self._camera_is_active = True
                    print(f"[{self.nom}]: PiCamera2 real iniciada i configurada amb {self._resolucio}.")
                except Exception as e:
                    print(f"[{self.nom} ERROR]: No s'ha pogut inicialitzar PiCamera2 real: {e}. Canviant a mode SIMULAT.")
                    self._is_real_camera_simulated = True # Forcem simulació si la real falla
                    self._camera_is_active = True # La simulació sempre s'activa
            
            if self._is_real_camera_simulated and not self._camera_is_active:
                # Si ja no estava activa i estem en mode simulat (o hi hem caigut)
                self._camera_is_active = True
                print(f"[{self.nom}]: Càmera operant en mode SIMULAT.")
        else:
            print(f"[{self.nom}]: La càmera ja estava activa en entrar al context.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Mètode que es crida quan se surt del bloc 'with',
        garantint que la càmera s'aturi i alliberi els recursos.
        """
        print(f"[{self.nom}]: Sortint del context. Aturant càmera...")
        self.stop_camera() # Utilitzem el mètode stop_camera per a una neteja consistent

    def __del__(self):
        """
        Mètode finalitzador. S'assegura que la càmera s'aturi si l'objecte
        és destruït pel recol·lector d'escombraries sense usar 'with'.
        """
        if self._camera_is_active: # Només intentem aturar si estava activa
            print(f"[{self.nom}]: Executant __del__ (aturant càmera com a salvaguarda).")
            self.stop_camera()

    def stop_camera(self):
        """
        Atura el flux de la càmera i allibera els recursos (real o simulada).
        """
        if self._is_real_camera_simulated:
            if self._camera_is_active:
                print(f"[{self.nom}]: Càmera simulada 'aturada'.")
                self._camera_is_active = False
            else:
                print(f"[{self.nom}]: Càmera simulada ja estava inactiva.")
        elif self._picam2_instance: # Càmera real
            if self._camera_is_active:
                print(f"[{self.nom}]: Aturant PiCamera2 real i alliberant recursos...")
                try:
                    self._picam2_instance.stop()
                    self._picam2_instance.close()
                    self._picam2_instance = None
                    self._camera_is_active = False
                    print(f"[{self.nom}]: PiCamera2 real aturada i recursos alliberats.")
                except Exception as e:
                    print(f"[{self.nom} ERROR]: Error aturant PiCamera2 real: {e}")
            else:
                print(f"[{self.nom}]: PiCamera2 real ja estava inactiva.")
                if self._picam2_instance: # Si la instància existeix però no està activa, la tanquem igualment
                    try:
                        self._picam2_instance.close()
                        self._picam2_instance = None
                    except Exception as e:
                        print(f"[{self.nom} ERROR]: Error tancant instància inactiva de PiCamera2: {e}")
        else:
            print(f"[{self.nom}]: No hi ha cap instància de càmera activa per aturar.")

    def capture_image_data(self) -> Optional[Tuple[np.ndarray, str, Dict[str, Any]]]:
        """
        Captura una imatge.

        Returns:
            Optional[Tuple[np.ndarray, str, Dict[str, Any]]]: 
                Tupla amb (dades_imatge, extensió, metadades) o None si hi ha un error.
                L'extensió no inclou el punt.
        """
        if not self._camera_is_active:
            print(f"[{self.nom} ERROR]: Càmera no activa. Utilitza 'with Camera(...):' per activar-la.")
            return None

        image_data: Optional[np.ndarray] = None
        current_metadata = self._default_metadata.copy() # Copia per no modificar les metadades per defecte

        if not self._is_real_camera_simulated and self._picam2_instance:
            try:
                image_data = self._picam2_instance.capture_array()
                print(f"[{self.nom}]: Imatge real capturada.")
                # Aquí podries afegir metadades reals de la càmera si Picamera2 les proporciona
                # current_metadata.update(self.picam2.metadata) 
            except Exception as e:
                print(f"[{self.nom} ERROR]: Error en captura PiCamera2 real: {e}. Retornant simulació.")
                # Fallback a simulació si la càmera real falla durant la captura
                image_data = np.random.randint(0, 256, size=(self._resolucio[1], self._resolucio[0], 3), dtype=np.uint8)
        else: # Mode simulat
            print(f"[{self.nom}]: SIMULACIÓ: Retornant imatge simulada {self._resolucio[0]}x{self._resolucio[1]}.")
            image_data = np.random.randint(0, 256, size=(self._resolucio[1], self._resolucio[0], 3), dtype=np.uint8)
        
        if image_data is not None:
            return image_data, self._default_extension, current_metadata
        return None

    def get_camera_status(self) -> bool:
        """
        Retorna l'estat actual de la càmera (True si està activa, False altrament).
        """
        return self._camera_is_active

    def get_default_extension(self) -> str:
        """Retorna l'extensió de fitxer per defecte de la càmera."""
        return self._default_extension

    def get_default_metadata(self) -> Dict[str, Any]:
        """Retorna una còpia de les metadades per defecte de la càmera."""
        return self._default_metadata.copy()
    
