import os
from picamera2 import Picamera2 # , Preview # Preview normalment només per depurar
from libcamera import controls # Potser no necessitem aquesta importació si no utilitzem controls directament
import time
# import atexit # Ja no necessari amb __enter__ / __exit__ i __del__
import numpy as np
from PIL import Image

from .CameraFileManager import CameraFileManager # Assegura't que el fitxer es diu camera_file_manager.py

class Camera:
    """
    Classe per controlar la càmera Raspberry Pi utilitzant Picamera2,
    amb gestió de fitxers integrada.
    Implementa el protocol de gestió de context per a una inicialització i tancament segurs.
    """

    def __init__(self, nom_camera: str = "RPi Camera", capture_dir: str = "camera_captures", 
                 default_prefix: str = "", scripts_folder_name: str = "scripts", 
                 data_folder_name: str = "dades"):
        """
        Inicialitza la classe Camera i el seu gestor de fitxers.
        La configuració i l'inici de la càmera es realitzen mitjançant __enter__.

        Args:
            nom_camera (str): Nom identificatiu per a la càmera.
            capture_dir (str): Directori base relatiu o absolut on es guardaran les captures.
                               Si és relatiu, es resoldrà dins de '<Directori_Projecte>/<data_folder_name>/'.
            default_prefix (str): Prefix per defecte per als noms de fitxer (passat al FileManager).
            scripts_folder_name (str): El nom de la carpeta que conté els scripts del projecte.
            data_folder_name (str): El nom de la carpeta de dades dins del projecte.
        """
        self.nom = nom_camera
        self.picam2 = None
        self._is_started = False # Nou estat per saber si la càmera està en marxa

        # Instanciem el gestor de fitxers
        self.file_manager = CameraFileManager(
            base_directory=capture_dir, 
            default_prefix=default_prefix,
            scripts_folder_name=scripts_folder_name,
            data_folder_name=data_folder_name    
        )

        print(f"[{self.nom}]: Classe de càmera inicialitzada. Utilitzeu 'with Camera(...) as cam:' per començar a operar.")

    def __enter__(self):
        """
        Mètode que es crida quan s'entra al bloc 'with'.
        Configura i inicia la càmera.
        """
        print(f"[{self.nom}]: Entrant al context. Configuració i inici de la càmera...")
        # Crida a setup_camera amb una configuració per defecte o amb arguments passats
        self.setup_camera() 
        self.start_camera()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Mètode que es crida quan se surt del bloc 'with',
        garantint que la càmera s'aturi i alliberi els recursos.
        """
        print(f"[{self.nom}]: Sortint del context. Aturant càmera i alliberant recursos...")
        self.stop_camera()
        # Si hi ha una excepció, la propaguem.
        # return False (per defecte si no es retorna res o es retorna False)
        
    def __del__(self):
        """
        Mètode finalitzador per assegurar que la càmera s'aturi si l'objecte
        és destruït pel recol·lector d'escombraries sense usar 'with'.
        """
        if self._is_started or (self.picam2 and self.picam2.started): # Comprovem ambdues banderes
            print(f"[{self.nom}]: Executant __del__ (aturant càmera com a salvaguarda).")
            self.stop_camera()

    def get_file_manager(self) -> CameraFileManager:
        """Retorna la instància del gestor de fitxers associada a la càmera."""
        return self.file_manager

    def set_file_manager(self, new_file_manager: CameraFileManager):
        """
        Estableix una nova instància de CameraFileManager per a aquesta càmera.
        Args:
            new_file_manager (CameraFileManager): La nova instància de CameraFileManager.
        Raises:
            TypeError: Si new_file_manager no és una instància de CameraFileManager.
        """
        if not isinstance(new_file_manager, CameraFileManager):
            raise TypeError("El gestor de fitxers ha de ser una instància de CameraFileManager.")
        self.file_manager = new_file_manager
        print(f"[{self.nom}]: Gestor de fitxers actualitzat.")

    def setup_camera(self, resolucio: tuple = (1280, 720), mode_preview: bool = False):
        """
        Configura la càmera amb la resolució i el mode de previsualització especificats.
        Si la càmera ja està configurada, l'atura i la reconfigura.

        Args:
            resolucio (tuple): Tupla (amplada, alçada) per a la resolució de la captura.
            mode_preview (bool): Si True, configura per a previsualització. Si False, per a captures fixes.
        """
        if self.picam2:
            print(f"[{self.nom}]: La càmera ja estava configurada. Aturant i reconfigurant.")
            self.stop_camera() # Aturem abans de reconfigurar

        self.picam2 = Picamera2()
        
        # S'hauria de considerar que les configuracions de "preview" i "still"
        # són mútuament excloents o requereixen una lògica més complexa.
        # Per a simplicitat, creem una configuració adequada per a captures fixes.
        # Si realment es necessita previsualització, s'hauria de cridar picam2.start_preview().
        if mode_preview:
            self.camera_config = self.picam2.create_preview_configuration(main={"size": resolucio})
            print(f"[{self.nom}]: Mode de previsualització actiu. Les captures seran més ràpides.")
        else:
            # Per a captures fixes, BGR888 és un bon format per a NumPy i PIL.
            self.camera_config = self.picam2.create_still_configuration(main={"size": resolucio, "format": "BGR888"})
            print(f"[{self.nom}]: Mode de captura fixa actiu (BGR888).")
                                                               
        self.picam2.configure(self.camera_config)
        print(f"[{self.nom}]: Càmera configurada amb resolució {resolucio}.")

    def start_camera(self, delay_startup: float = 2):
        """
        Inicia el flux de la càmera.

        Args:
            delay_startup (float): Temps en segons per esperar que la càmera s'estabilitzi.
        """
        if not self.picam2:
            print(f"[{self.nom}]: La càmera no està configurada. Crida a 'setup_camera()' primer.")
            return

        if self._is_started:
            print(f"[{self.nom}]: La càmera ja està en marxa.")
            return

        try:
            self.picam2.start()
            self._is_started = True
            print(f"[{self.nom}]: Càmera iniciada. Esperant {delay_startup} segons per estabilitzar...")
            time.sleep(delay_startup)
            print(f"[{self.nom}]: Càmera estabilitzada.")
        except Exception as e:
            print(f"[{self.nom} ERROR]: No s'ha pogut iniciar la càmera: {e}")
            self._is_started = False # Assegurem que l'estat és correcte

    def save_image(self, extension: str = "jpg") -> str | None:
        """
        Captura una imatge i la guarda utilitzant el gestor de fitxers.

        Args:
            extension (str): Extensió del fitxer per a la imatge (e.g., "jpg", "png").

        Returns:
            str | None: La ruta completa del fitxer guardat, o None si hi ha un error.
        """
        if not self._is_started:
            print(f"[{self.nom}]: La càmera no està en marxa. Crida a 'start_camera()' primer.")
            return None

        try:
            # Captura un array NumPy des del flux principal (main)
            image_array = self.picam2.capture_array() 
        except Exception as e:
            print(f"[{self.nom} ERROR]: Error en capturar les dades de la imatge: {e}")
            return None

        full_filepath = self.file_manager.save_image_data(image_array, extension=extension)
        
        if full_filepath:
            print(f"[{self.nom}]: Imatge capturada i guardada per FileManager a: {full_filepath}")
            return full_filepath
        else:
            print(f"[{self.nom} ERROR]: FileManager no va poder guardar la imatge.")
            return None

    def stop_camera(self):
        """
        Atura el flux de la càmera i allibera els recursos.
        """
        if self.picam2 and self._is_started:
            print(f"[{self.nom}]: Aturant càmera i alliberant recursos...")
            try:
                self.picam2.stop()
                self.picam2.close() # Tanca l'instància de Picamera2
                self.picam2 = None
                self._is_started = False
                print(f"[{self.nom}]: Càmera aturada i recursos alliberats.")
            except Exception as e:
                print(f"[{self.nom} ERROR]: Error en aturar la càmera: {e}")
        elif self.picam2 and not self._is_started:
            print(f"[{self.nom}]: La càmera ja no estava en marxa, però la instància existia. Tancant-la.")
            try:
                self.picam2.close()
                self.picam2 = None
            except Exception as e:
                print(f"[{self.nom} ERROR]: Error en tancar la instància de la càmera: {e}")
        else:
            print(f"[{self.nom}]: No hi ha cap instància de càmera activa per aturar.")

    def get_camera_status(self) -> bool:
        """
        Retorna l'estat actual de la càmera (True si està iniciada, False altrament).
        """
        return self._is_started

    def get_capture_history(self) -> list:
        """
        Retorna la llista de rutes de les captures de la càmera.
        """
        return self.file_manager.get_capture_history()

    def get_last_capture_path(self) -> str | None:
        """
        Retorna la ruta de l'última captura.
        """
        return self.file_manager.get_last_capture()

    def clear_capture_history(self):
        """
        Neteja l'historial de captures del gestor de fitxers.
        """
        self.file_manager.clear_history()

    def delete_captured_file(self, filepath: str) -> bool:
        """
        Elimina un fitxer de captura del disc i de l'historial.

        Args:
            filepath (str): La ruta completa del fitxer a eliminar.

        Returns:
            bool: True si el fitxer s'ha eliminat amb èxit, False altrament.
        """
        return self.file_manager.delete_capture_file(filepath)
    
   
