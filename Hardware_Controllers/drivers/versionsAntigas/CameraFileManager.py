import os
import json
from datetime import datetime
import numpy as np
from PIL import Image

class CameraFileManager:
    """
    Classe per gestionar l'emmagatzematge i l'historial de les imatges capturades per la càmera.
    L'historial es guarda automàticament en un fitxer JSON.
    """
    def __init__(self, base_directory: str = "camera_captures", default_prefix: str = "",
                 scripts_folder_name: str = "scripts", data_folder_name: str = "dades"):
        """
        Inicialitza el gestor de fitxers.

        Args:
            base_directory (str): El directori relatiu o absolut on es guardaran les captures.
                                  Si és relatiu, es resoldrà dins de '<Directori_Projecte>/<data_folder_name>/'.
                                  Es crearà si no existeix.
            default_prefix (str): Prefix per defecte a utilitzar en els noms de fitxer generats.
                                  Només es pot definir en la inicialització.
            scripts_folder_name (str): El nom de la carpeta que conté els scripts del projecte (e.g., 'scripts').
                                       S'utilitza per trobar l'arrel del projecte.
            data_folder_name (str): El nom de la carpeta de dades dins del projecte (e.g., 'dades').
                                    Les captures es guardaran dins d'aquesta carpeta.
        """
        self._default_prefix = default_prefix
        self._scripts_folder_name = scripts_folder_name
        self._data_folder_name = data_folder_name
        self.capture_history = []
        self._base_directory = "" # S'inicialitzarà correctament més tard

        # Resolem la ruta del directori base en funció de la nova lògica
        self._set_and_resolve_base_directory(base_directory)

        self._history_filename = self._get_history_filename()
        self._load_history_from_disk()
        
        print(f"[FileManager]: Gestor de fitxers inicialitzat. Directori base: '{self._base_directory}', Prefix: '{self._default_prefix}'")
        print(f"[FileManager]: Carpeta de scripts: '{self._scripts_folder_name}', Carpeta de dades: '{self._data_folder_name}'.")

    def __del__(self):
        """
        Mètode finalitzador per assegurar que l'historial es guarda
        si l'objecte és destruït sense una crida explícita a _save_history_to_disk.
        """
        print(f"[FileManager]: Executant __del__ (guardant historial com a salvaguarda).")
        self._save_history_to_disk()

    def _find_project_root(self, current_path: str, marker_folder: str) -> str | None:
        """
        Intenta trobar el directori arrel del projecte buscant una carpeta 'marker_folder'
        pujant en la jerarquia de directoris.
        """
        path = os.path.abspath(current_path)
        # Bucle per buscar la carpeta marcador pujant en la jerarquia de directoris
        while True:
            if os.path.isdir(os.path.join(path, marker_folder)):
                return path # Hem trobat l'arrel del projecte
            parent_path = os.path.dirname(path)
            if parent_path == path: # Hem arribat a l'arrel del sistema de fitxers
                return None
            path = parent_path

    def _set_and_resolve_base_directory(self, provided_base_directory: str):
        """
        Resol la ruta final del directori base per a les captures i l'estableix com a _base_directory.
        Si la ruta és relativa, la situa dins de <Directori_Projecte>/<data_folder_name>/.
        També s'assegura que el directori existeixi.
        """
        if os.path.isabs(provided_base_directory):
            print(f"[FileManager]: Directori base proporcionat com a absolut: '{provided_base_directory}'.")
            self._base_directory = provided_base_directory
        else:
            print(f"[FileManager]: Directori base proporcionat com a relatiu: '{provided_base_directory}'. Intentant trobar l'arrel del projecte.")
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Utilitza self._scripts_folder_name per trobar l'arrel del projecte
            project_root = self._find_project_root(script_dir, self._scripts_folder_name)

            if project_root:
                print(f"[FileManager]: Arrel del projecte trobada a: '{project_root}'.")
                # Utilitza self._data_folder_name per construir la ruta a la carpeta de dades
                data_dir = os.path.join(project_root, self._data_folder_name)
                self._ensure_directory_exists(data_dir) # Assegura que la carpeta de dades existeix
                
                final_base_dir = os.path.join(data_dir, provided_base_directory)
                self._base_directory = final_base_dir
                print(f"[FileManager]: Directori de captures relatiu resolt a: '{self._base_directory}'.")
            else:
                print(f"[FileManager WARNING]: No s'ha pogut trobar el directori arrel del projecte ('{self._scripts_folder_name}' folder).")
                print(f"[FileManager WARNING]: Les captures es guardaran en una subcarpeta de l'actual directori de treball: '{os.path.abspath(provided_base_directory)}'.")
                self._base_directory = os.path.abspath(provided_base_directory)
        
        # Assegurem que el directori final existeix
        self._ensure_directory_exists(self._base_directory)


    # --- Getters i Setters per a base_directory ---
    def get_base_directory(self) -> str:
        """Retorna la ruta base actual on es guarden les captures."""
        return self._base_directory

    def set_base_directory(self, new_directory: str):
        """
        Canvia el directori base per a les captures.
        Això desarà l'historial del directori antic i carregarà/iniciarà un nou historial
        per al nou directori.

        Args:
            new_directory (str): La nova ruta del directori base.
        Raises:
            ValueError: Si la ruta és buida o no és una cadena.
        """
        if not isinstance(new_directory, str) or not new_directory.strip():
            raise ValueError("El directori base ha de ser una cadena de text no buida.")
        
        print(f"[FileManager]: Canviant de directori. Guardant historial antic a '{self._base_directory}'...")
        self._save_history_to_disk() # Guarda l'historial actual abans de canviar de directori

        old_base_directory = self._base_directory
        # La resolució del directori i la creació de carpetes es fa aquí
        self._set_and_resolve_base_directory(new_directory) 
        
        # El nom del fitxer d'historial podria canviar si el prefix és diferent
        self._history_filename = self._get_history_filename()

        self.capture_history = [] # Neteja l'historial en RAM
        print(f"[FileManager]: Historial en RAM netejat per al nou directori.")

        self._load_history_from_disk() # Carrega l'historial del nou directori
        
        print(f"[FileManager]: Directori base actualitzat de '{old_base_directory}' a '{self._base_directory}'.")

    # --- Getter per al prefix per defecte (no setter, ja que es defineix en la inicialització) ---
    def get_default_prefix(self) -> str:
        """Retorna el prefix per defecte utilitzat en els noms de fitxer."""
        return self._default_prefix

    def _get_history_filename(self) -> str:
        """Genera el nom del fitxer d'historial basat en el prefix per defecte."""
        if self._default_prefix:
            return f"historial-{self._default_prefix}.json"
        else:
            return "historial.json"

    def _get_history_filepath(self) -> str:
        """Retorna la ruta completa al fitxer d'historial."""
        return os.path.join(self._base_directory, self._history_filename)

    def _ensure_directory_exists(self, directory_path: str):
        """
        Crea un directori si no existeix.
        Args:
            directory_path (str): La ruta del directori a crear.
        """
        if not os.path.exists(directory_path):
            try:
                os.makedirs(directory_path, exist_ok=True) # exist_ok=True evita errors si ja existeix
                print(f"[FileManager]: Directori '{directory_path}' creat.")
            except OSError as e:
                print(f"[FileManager ERROR]: No s'ha pogut crear el directori '{directory_path}': {e}")
                raise # Re-llancem l'excepció perquè és un error crític

    def _generate_unique_filename(self, extension: str = "jpg") -> str:
        """
        Genera un nom de fitxer únic basat en la data i hora actuals i el prefix.
        Args:
            extension (str): L'extensió del fitxer.
        Returns:
            str: El nom de fitxer generat.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f") # Afegim mil·lisegons per més unicitat
        if self._default_prefix:
            return f"{self._default_prefix}_{timestamp}.{extension}"
        else:
            return f"{timestamp}.{extension}"

    def _get_full_path(self, filename: str) -> str:
        """
        Construeix la ruta completa a un fitxer donat el seu nom.
        Args:
            filename (str): El nom del fitxer.
        Returns:
            str: La ruta completa del fitxer.
        """
        return os.path.join(self._base_directory, filename)

    def get_new_filepath(self, extension: str = "jpg") -> str:
        """
        Obté una nova ruta de fitxer única on es pot guardar una captura.
        Args:
            extension (str): L'extensió del fitxer.
        Returns:
            str: La ruta completa suggerida per a un nou fitxer.
        """
        filename = self._generate_unique_filename(extension=extension)
        full_filepath = self._get_full_path(filename)
        return full_filepath

    def save_image_data(self, image_data: np.ndarray, extension: str = "jpg") -> str | None:
        """
        Guarda les dades de la imatge (array NumPy) a un fitxer.
        També afegeix la ruta del fitxer a l'historial.

        Args:
            image_data (np.ndarray): Les dades de la imatge com a array NumPy.
            extension (str): L'extensió del fitxer (e.g., "jpg", "png").

        Returns:
            str | None: La ruta completa del fitxer guardat, o None si hi ha un error.
        """
        if not isinstance(image_data, np.ndarray):
            print("[FileManager ERROR]: Les dades de la imatge no són un array NumPy.")
            return None

        full_filepath = self.get_new_filepath(extension=extension)

        try:
            # Convertim l'array NumPy a una imatge PIL
            img = Image.fromarray(image_data)
            
            # Assegurem que la imatge tingui el mode correcte (RGB/RGBA per a la majoria de formats)
            # Picamera2 sol retornar BGR888 per defecte en 'still' mode
            if img.mode == 'BGR': 
                img = img.convert('RGB')
            elif img.mode == 'BGRA':
                img = img.convert('RGBA')

            img.save(full_filepath)
            
            self.record_capture(full_filepath)
            return full_filepath
        except Exception as e:
            print(f"[FileManager ERROR]: No s'ha pogut guardar la imatge a '{full_filepath}': {e}")
            return None

    def _save_history_to_disk(self):
        """
        Guarda l'historial de captures actual a un fitxer JSON al disc.
        """
        history_filepath = self._get_history_filepath()

        if not self.capture_history:
            print(f"[FileManager]: No hi ha historial per guardar a '{history_filepath}'.")
            # Si no hi ha historial, eliminem el fitxer JSON existent per netejar
            if os.path.exists(history_filepath):
                try:
                    os.remove(history_filepath)
                    print(f"[FileManager]: Fitxer d'historial buit '{history_filepath}' eliminat.")
                except OSError as e:
                    print(f"[FileManager ERROR]: No s'ha pogut eliminar el fitxer d'historial buit '{history_filepath}': {e}")
            return

        try:
            # Assegura que el directori de l'historial existeix abans de guardar
            self._ensure_directory_exists(os.path.dirname(history_filepath))
            with open(history_filepath, 'w') as f:
                json.dump(self.capture_history, f, indent=4)
            print(f"[FileManager]: Historial guardat a '{history_filepath}'.")
        except IOError as e:
            print(f"[FileManager ERROR]: No s'ha pogut guardar l'historial a '{history_filepath}': {e}")

    def _load_history_from_disk(self):
        """
        Carrega l'historial de captures des d'un fitxer JSON al disc.
        """
        history_filepath = self._get_history_filepath()

        if os.path.exists(history_filepath):
            try:
                with open(history_filepath, 'r') as f:
                    loaded_history = json.load(f)
                    if isinstance(loaded_history, list) and all(isinstance(item, str) for item in loaded_history):
                        self.capture_history = loaded_history
                        print(f"[FileManager]: Historial carregat des de '{history_filepath}'.")
                    else:
                        print(f"[FileManager WARNING]: Fitxer d'historial corrupte o format incorrecte a '{history_filepath}'. Iniciant historial buit.")
                        self.capture_history = []
            except (IOError, json.JSONDecodeError) as e:
                print(f"[FileManager ERROR]: No s'ha pogut carregar l'historial des de '{history_filepath}': {e}. Iniciant historial buit.")
                self.capture_history = []
        else:
            print(f"[FileManager]: No s'ha trobat fitxer d'historial a '{history_filepath}'. Iniciant historial buit.")
            self.capture_history = []

    def record_capture(self, full_filepath: str):
        """
        Afegeix una ruta de fitxer a l'historial de captures i el guarda al disc.
        Args:
            full_filepath (str): La ruta completa del fitxer de la captura.
        """
        self.capture_history.append(full_filepath)
        print(f"[FileManager]: '{os.path.basename(full_filepath)}' afegida a l'historial.")
        self._save_history_to_disk()

    def get_last_capture(self) -> str | None:
        """
        Retorna la ruta de l'última captura registrada a l'historial.
        Returns:
            str | None: La ruta de l'última captura, o None si l'historial està buit.
        """
        return self.capture_history[-1] if self.capture_history else None

    def get_capture_history(self) -> list:
        """
        Retorna una còpia de la llista de l'historial de captures.
        Returns:
            list: Una llista amb les rutes de les captures.
        """
        return list(self.capture_history) # Retorna una còpia per evitar modificacions externes directes

    def clear_history(self):
        """
        Neteja l'historial de captures (tant en RAM com al disc).
        """
        self.capture_history = []
        self._save_history_to_disk() # Això eliminarà el fitxer d'historial si està buit
        print("[FileManager]: Historial de captures netejat (RAM i disc).")

    def delete_capture_file(self, filepath: str) -> bool:
        """
        Elimina un fitxer de captura del disc i de l'historial.
        Args:
            filepath (str): La ruta completa del fitxer a eliminar.
        Returns:
            bool: True si el fitxer s'ha eliminat amb èxit, False altrament.
        """
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                if filepath in self.capture_history:
                    self.capture_history.remove(filepath)
                    self._save_history_to_disk() # Guarda l'historial actualitzat
                print(f"[FileManager]: Fitxer '{os.path.basename(filepath)}' eliminat del disc i historial.")
                return True
            except OSError as e:
                print(f"[FileManager ERROR]: No s'ha pogut eliminar '{os.path.basename(filepath)}': {e}")
                return False
        else:
            print(f"[FileManager]: Fitxer '{os.path.basename(filepath)}' no trobat per eliminar.")
            return False
