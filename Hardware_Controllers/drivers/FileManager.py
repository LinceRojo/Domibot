import os
import json
import datetime
import shutil 
import numpy as np
from PIL import Image
import soundfile as sf

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Union, Dict

#if TYPE_CHECKING:
from .controladors.Camera import Camera
from .controladors.Microphone import Microphone
from .controladors.Altaveu import Altaveu


class FileManager:
    """
    Classe central per gestionar l'emmagatzematge de fitxers (imatges, àudio)
    i orquestrar les operacions de maquinari (càmera, micròfon, altaveu)
    a través de les seves respectives classes registrades.
    Manté un historial de captures i reproduccions en un fitxer JSON.
    """
    PROJECT_ROOT_MARKER_FILENAME = ".project_root" # Fitxer marcador per identificar l'arrel del projecte

    def __init__(self, base_directory: str = "captures", default_prefix: str = "",
                 scripts_folder_name: str = "scripts", data_folder_name: str = "dades"):
        """
        Inicialitza el Gestor de Fitxers.

        Args:
            base_directory (str): Nom del subdirectori dins de la carpeta de dades
                                  on es guardaran les captures (ex: "captures").
                                  Pot ser una ruta absoluta.
            default_prefix (str): Prefix per defecte per als noms de fitxer generats.
            scripts_folder_name (str): Nom de la carpeta que conté els scripts del projecte.
                                       S'utilitza per trobar l'arrel del projecte.
            data_folder_name (str): Nom de la carpeta de dades dins de l'arrel del projecte.
                                    Les captures es guardaran dins d'aquesta carpeta.
        """
        self._default_prefix = default_prefix.strip().replace(" ", "_") # Neteja el prefix
        self._scripts_folder_name = scripts_folder_name
        self._data_folder_name = data_folder_name
        
        self._project_root: Optional[str] = None
        self._base_directory_path: str = "" # Ruta absoluta final del directori de captures

        # Resolem les rutes i assegurem que els directoris existeixen
        self._resolve_paths_and_ensure_dirs(base_directory)

        self._history_filename: str = self._generate_history_filename()
        self.capture_history: List[Dict[str, Any]] = [] # L'historial ara conté diccionaris
        self._load_history_from_disk()
        
        # Instàncies de maquinari registrades
        self._camera: Optional['Camera'] = None
        self._microphone: Optional['Microphone'] = None
        self._speaker: Optional['Altaveu'] = None 

        print(f"[FileManager ({self._default_prefix})]: Gestor inicialitzat. Directori base: '{self._base_directory_path}'.")
        print(f"[FileManager ({self._default_prefix})]: Arrel projecte: '{self._project_root}'.")

    def __enter__(self):
        """
        Mètode que es crida quan s'entra al bloc 'with'.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        S'executa quan es surt del bloc 'with', fins i tot si hi ha una exc>        Garanteix la neteja dels pins GPIO.
        """
        pass

    def __del__(self):
        """
        Mètode finalitzador. S'assegura que l'historial es guarda al disc
        quan l'objecte FileManager és destruït.
        """
        print(f"[FileManager ({self._default_prefix})]: Executant __del__ (guardant historial com a salvaguarda).")
        self._save_history_to_disk()

    # --- Gestió de Rutes i Directoris ---
    def _find_project_root_path(self) -> str:
        """
        Intenta trobar el directori arrel del projecte.
        Busca un fitxer marcador (.project_root) o la carpeta de scripts/dades
        pujant en la jerarquia de directoris des de la ubicació del script actual.
        """
        current_script_dir = os.path.abspath(os.path.dirname(__file__))
        path_to_check = current_script_dir

        # Estratègia 1: Buscar el fitxer marcador .project_root
        while True:
            if os.path.exists(os.path.join(path_to_check, self.PROJECT_ROOT_MARKER_FILENAME)):
                print(f"[FileManager ({self._default_prefix})]: Arrel del projecte trobada per marcador: '{path_to_check}'.")
                return path_to_check
            parent = os.path.dirname(path_to_check)
            if parent == path_to_check: # Hem arribat a l'arrel del sistema de fitxers
                break
            path_to_check = parent
        
        # Estratègia 2: Buscar la carpeta de scripts o de dades
        path_to_check = current_script_dir
        while True:
            if os.path.isdir(os.path.join(path_to_check, self._scripts_folder_name)) and \
               os.path.isdir(os.path.join(path_to_check, self._data_folder_name)):
                print(f"[FileManager ({self._default_prefix})]: Arrel del projecte trobada per carpetes: '{path_to_check}'.")
                return path_to_check
            parent = os.path.dirname(path_to_check)
            if parent == path_to_check: # Hem arribat a l'arrel del sistema de fitxers
                break
            path_to_check = parent

        print(f"[FileManager ({self._default_prefix}) WARNING]: No s'ha pogut determinar l'arrel del projecte robustament. Utilitzant el directori de treball actual: {os.getcwd()}")
        return os.getcwd() # Últim recurs: el directori de treball actual

    def _resolve_paths_and_ensure_dirs(self, provided_base_dir_name: str):
        """
        Resol la ruta absoluta del directori base de captures i s'assegura que existeix.
        """
        self._project_root = self._find_project_root_path()
        
        # Ruta a la carpeta de dades dins de l'arrel del projecte
        project_data_dir = os.path.join(self._project_root, self._data_folder_name)
        self._ensure_directory_exists(project_data_dir) # Assegura que la carpeta de dades existeix

        if os.path.isabs(provided_base_dir_name):
            self._base_directory_path = provided_base_dir_name
            print(f"[FileManager ({self._default_prefix})]: Directori base absolut: '{self._base_directory_path}'.")
        else:
            self._base_directory_path = os.path.join(project_data_dir, provided_base_dir_name)
            print(f"[FileManager ({self._default_prefix})]: Directori base relatiu resolt a: '{self._base_directory_path}'.")
        
        self._ensure_directory_exists(self._base_directory_path) # Assegura que el directori de captures existeix

    def _ensure_directory_exists(self, directory_path: str):
        """
        Crea un directori si no existeix. Llença OSError si no es pot crear.
        """
        if not os.path.exists(directory_path):
            try:
                os.makedirs(directory_path, exist_ok=True)
                print(f"[FileManager ({self._default_prefix})]: Directori '{directory_path}' creat.")
            except OSError as e:
                print(f"[FileManager ({self._default_prefix}) ERROR]: No s'ha pogut crear el directori '{directory_path}': {e}")
                raise # Re-llancem l'excepció perquè és un error crític

    def set_base_directory(self, new_base_dir_name: str):
        """
        Canvia el directori base per a les captures.
        Guarda l'historial del directori antic i carrega/inicia un nou historial
        per al nou directori.

        Args:
            new_base_dir_name (str): El nom del nou subdirectori dins de la carpeta de dades.
        Raises:
            ValueError: Si el nom del directori és buit o no és una cadena.
        """
        if not isinstance(new_base_dir_name, str) or not new_base_dir_name.strip():
            raise ValueError("El nom del directori base ha de ser una cadena no buida.")
        
        print(f"[FileManager ({self._default_prefix})]: Canviant directori base. Guardant historial antic...")
        self._save_history_to_disk() # Guarda l'historial de la ubicació ANTIGA

        old_base_path = self._base_directory_path
        self._resolve_paths_and_ensure_dirs(new_base_dir_name) # Resoldre i crear el nou directori
        
        self._history_filename = self._generate_history_filename() # Generar nom d'historial per al nou directori
        self.capture_history = [] # Netejar historial en RAM
        self._load_history_from_disk() # Carregar historial de la NOVA ubicació
        
        print(f"[FileManager ({self._default_prefix})]: Directori base actualitzat de '{old_base_path}' a '{self._base_directory_path}'.")

    # --- Maquinari: Registre ---
    def register_camera(self, camera_instance: 'Camera'):
        """
        Registra una instància de la classe Camera amb el FileManager.
        Args:
            camera_instance (Camera): Instància de la classe Camera.
        Raises:
            ValueError: Si l'objecte no té el mètode 'capture_image_data'.
        """
        if not (hasattr(camera_instance, 'capture_image_data') and callable(camera_instance.capture_image_data)):
            raise ValueError("Objecte camera invàlid: falta el mètode 'capture_image_data'.")
        self._camera = camera_instance
        print(f"[FileManager ({self._default_prefix})]: Càmera '{getattr(camera_instance, 'nom', 'N/A')}' registrada.")

    def register_microphone(self, microphone_instance: 'Microphone'):
        """
        Registra una instància de la classe Microphone amb el FileManager.
        Args:
            microphone_instance (Microphone): Instància de la classe Microphone.
        Raises:
            ValueError: Si l'objecte no té el mètode 'record_audio_data'.
        """
        if not (hasattr(microphone_instance, 'record_audio_data') and callable(microphone_instance.record_audio_data)):
            raise ValueError("Objecte microphone invàlid: falta el mètode 'record_audio_data'.")
        self._microphone = microphone_instance
        print(f"[FileManager ({self._default_prefix})]: Micròfon '{getattr(microphone_instance, 'nom', 'N/A')}' registrat.")

    def register_speaker(self, speaker_instance: 'Altaveu'):
        """
        Registra una instància de la classe Altaveu amb el FileManager.
        Args:
            speaker_instance (Altaveu): Instància de la classe Altaveu.
        Raises:
            TypeError: Si la instància no és del tipus Altaveu (si està disponible).
            ValueError: Si l'objecte no té el mètode 'play_audio_file'.
        """

        if not (hasattr(speaker_instance, 'play_audio_file') and callable(speaker_instance.play_audio_file)):
            raise ValueError("Objecte speaker invàlid: falta el mètode 'play_audio_file'.")
        self._speaker = speaker_instance
        print(f"[FileManager ({self._default_prefix})]: Altaveu '{getattr(speaker_instance, 'nom', 'N/A')}' registrat.")

    # --- Generació de Noms i Guardat Genèric ---
    def _generate_filename(self, content_type: str, extension: str) -> str:
        """
        GenAltaveuera un nom de fitxer únic basat en el tipus de contingut, la data/hora i el prefix.
        Args:
            content_type (str): Tipus de contingut (ex: "imatge", "audio").
            extension (str): Extensió del fitxer (sense el punt).
        Returns:
            str: El nom de fitxer generat.
        """
        # Afegim mil·lisegons per a més unicitat
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3] 
        prefix_part = f"{self._default_prefix}_" if self._default_prefix else ""
        return f"{prefix_part}{content_type}_{timestamp}.{extension}"

    def _save_data_and_log(self, data_to_save: Any, filepath: str,
                           content_type: str, metadata: Dict[str, Any],
                           save_function: callable) -> Optional[str]:
        """
        Funció genèrica per desar dades i actualitzar l'historial.
        Args:
            data_to_save (Any): Les dades a guardar (format depèn de save_function).
            filepath (str): La ruta completa on guardar el fitxer.
            content_type (str): Tipus de contingut (per a l'historial).
            metadata (Dict[str, Any]): Metadades a associar amb l'entrada de l'historial.
            save_function (callable): Funció que realitza el guardat real (ex: PIL.Image.save, sf.write).
                                      Ha d'acceptar (filepath, data_to_save).
        Returns:
            Optional[str]: La ruta del fitxer guardat si té èxit, None altrament.
        """
        try:
            save_function(filepath, data_to_save)
            self._add_to_history(filepath, content_type, metadata)
            print(f"[FileManager ({self._default_prefix})]: {content_type.capitalize()} guardat a '{filepath}'.")
            return filepath
        except Exception as e:
            print(f"[FileManager ({self._default_prefix}) ERROR]: No s'ha pogut guardar {content_type} a '{filepath}': {e}")
            return None

    # --- Maquinari: Control i Operacions ---
    def take_photo(self) -> Optional[str]:
        """
        Captura una imatge utilitzant la càmera registrada i la guarda.
        Retorna la ruta del fitxer guardat o None en cas d'error.
        """
        if not self._camera:
            print(f"[FileManager ({self._default_prefix}) ERROR]: Càmera no registrada. No es pot prendre una foto.")
            return None
        try:
            # capture_image_data retorna (image_data, extension, metadata)
            capture_result = self._camera.capture_image_data()
            if capture_result:
                image_data, extension, metadata = capture_result
                filepath = os.path.join(self._base_directory_path, self._generate_filename("imatge", extension))
                
                # Funció de guardat específica per a imatges (PIL)
                def save_img_func(fp, data):
                    img = Image.fromarray(data)
                    if img.mode == 'BGR': img = img.convert('RGB')
                    elif img.mode == 'BGRA': img = img.convert('RGBA')
                    img.save(fp)

                return self._save_data_and_log(image_data, filepath, "imatge", metadata, save_img_func)
            else:
                print(f"[FileManager ({self._default_prefix}) ERROR]: La càmera no ha retornat dades d'imatge vàlides.")
                return None
        except Exception as e:
            print(f"[FileManager ({self._default_prefix}) ERROR]: Error durant la captura de foto: {e}")
            return None

    def record_audio(self, duration: int = 5) -> Optional[str]:
        """
        Grava àudio utilitzant el micròfon registrat i el guarda.
        Retorna la ruta del fitxer guardat o None en cas d'error.
        Args:
            duration (int): Durada de la gravació en segons.
        """
        if not self._microphone:
            print(f"[FileManager ({self._default_prefix}) ERROR]: Micròfon no registrat. No es pot gravar àudio.")
            return None
        try:
            # record_audio_data retorna (audio_data, samplerate, extension, metadata)
            capture_result = self._microphone.record_audio_data(duration)
            if capture_result:
                audio_data, samplerate, extension, metadata = capture_result
                
                # Afegir metadades pròpies de l'àudio si no s'han passat
                full_metadata = {
                    "samplerate": samplerate, 
                    "channels": audio_data.ndim, 
                    "duration_seconds": len(audio_data)/samplerate if samplerate > 0 else 0
                }
                full_metadata.update(metadata) # Combinar amb les metadades del micròfon

                filepath = os.path.join(self._base_directory_path, self._generate_filename("audio", extension))
                
                # Funció de guardat específica per a àudio (soundfile)
                def save_audio_func(fp, data_tuple):
                    # data_tuple és (audio_data, samplerate) per a sf.write
                    sf.write(fp, data_tuple[0], data_tuple[1])

                return self._save_data_and_log((audio_data, samplerate), filepath, "audio", full_metadata, save_audio_func)
            else:
                print(f"[FileManager ({self._default_prefix}) ERROR]: El micròfon no ha retornat dades d'àudio vàlides.")
                return None
        except Exception as e:
            print(f"[FileManager ({self._default_prefix}) ERROR]: Error durant la gravació d'àudio: {e}")
            return None

    def play_audio_from_history(self, identifier: Union[str, int]) -> bool:
        """
        Reprodueix un fitxer d'àudio de l'historial utilitzant l'altaveu registrat.
        Args:
            identifier (Union[str, int]): Nom del fitxer o índex de l'entrada a l'historial.
        Returns:
            bool: True si la reproducció s'inicia amb èxit, False altrament.
        """
        if not self._speaker:
            print(f"[FileManager ({self._default_prefix}) ERROR]: Altaveu no registrat. No es pot reproduir àudio.")
            return False
        
        entry = self.get_capture_entry_by_identifier(identifier, content_type_filter="audio")
        if entry and entry.get("filepath"):
            audio_filepath = entry["filepath"]
            try:
                # play_audio_file gestiona la reproducció i retorna True/False
                return self._speaker.play_audio_file(audio_filepath)
            except Exception as e:
                print(f"[FileManager ({self._default_prefix}) ERROR]: Error reproduint '{audio_filepath}': {e}")
                return False
        else:
            print(f"[FileManager ({self._default_prefix}) ERROR]: No s'ha trobat entrada d'àudio amb identificador '{identifier}'.")
            return False

    # --- Gestió d'Historial ---
    def _generate_history_filename(self) -> str:
        """
        Genera la ruta completa al fitxer d'historial JSON.
        El nom del fitxer depèn del prefix per defecte.
        """
        prefix_part = f"historial_{self._default_prefix}" if self._default_prefix else "historial"
        # Assegura que _base_directory_path està definit abans de cridar això
        return os.path.join(self._base_directory_path, f"{prefix_part}.json")

    def _add_to_history(self, filepath: str, content_type: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Afegeix una nova entrada a l'historial de captures i la guarda al disc.
        """
        entry = {
            "filepath": os.path.abspath(filepath),
            "filename": os.path.basename(filepath),
            "timestamp": datetime.datetime.now().isoformat(),
            "content_type": content_type,
            "metadata": metadata or {}
        }
        self.capture_history.append(entry)
        self._save_history_to_disk() # Guarda l'historial actualitzat al disc

    def _save_history_to_disk(self):
        """
        Guarda l'historial de captures actual a un fitxer JSON al disc.
        Crea el directori si no existeix.
        """
        history_filepath = self._generate_history_filename()
        try:
            self._ensure_directory_exists(os.path.dirname(history_filepath)) # Assegura que el directori de l'historial existeix
            with open(history_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.capture_history, f, indent=4)
            print(f"[FileManager ({self._default_prefix})]: Historial guardat a '{history_filepath}'.")
        except Exception as e:
            print(f"[FileManager ({self._default_prefix}) ERROR]: Error guardant historial a '{history_filepath}': {e}")

    def _load_history_from_disk(self):
        """
        Carrega l'historial de captures des d'un fitxer JSON al disc.
        Si el fitxer no existeix o està corrupte, inicia un historial buit.
        """
        history_filepath = self._generate_history_filename()
        if os.path.exists(history_filepath):
            try:
                with open(history_filepath, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Validació bàsica del format de l'historial
                    if isinstance(loaded_data, list) and \
                       all(isinstance(item, dict) and 'filepath' in item and 'content_type' in item for item in loaded_data):
                        self.capture_history = loaded_data
                        print(f"[FileManager ({self._default_prefix})]: Historial carregat ({len(self.capture_history)} entrades) des de '{history_filepath}'.")
                    else: # Format incorrecte
                        self.capture_history = []
                        print(f"[FileManager ({self._default_prefix}) WARNING]: Fitxer d'historial corrupte o format incorrecte a '{history_filepath}'. Iniciant nou historial.")
                        self._save_history_to_disk() # Guarda el nou historial buit
            except (json.JSONDecodeError, IOError) as e:
                self.capture_history = []
                print(f"[FileManager ({self._default_prefix}) ERROR]: Error carregant historial des de '{history_filepath}': {e}. Iniciant nou historial.")
                self._save_history_to_disk() # Guarda el nou historial buit
        else: # No existeix el fitxer d'historial
            self.capture_history = []
            print(f"[FileManager ({self._default_prefix})]: Fitxer historial '{history_filepath}' no trobat. Iniciant nou historial.")
            self._save_history_to_disk() # Guarda el nou historial buit

    def get_capture_history(self, content_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna una còpia de la llista de l'historial de captures, opcionalment filtrada per tipus de contingut.
        Args:
            content_type_filter (Optional[str]): Si es proporciona, filtra per aquest tipus de contingut (ex: "imatge", "audio").
        Returns:
            List[Dict[str, Any]]: Una llista de diccionaris, cada un representant una entrada de l'historial.
        """
        history_copy = list(self.capture_history) # Retorna una còpia per evitar modificacions externes directes
        if content_type_filter:
            return [entry for entry in history_copy if entry.get("content_type") == content_type_filter]
        return history_copy

    def get_capture_entry_by_identifier(self, identifier: Union[str, int], content_type_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Cerca una entrada a l'historial per nom de fitxer o índex.
        Args:
            identifier (Union[str, int]): Nom del fitxer (string) o índex (int) a l'historial.
            content_type_filter (Optional[str]): Filtra per tipus de contingut (ex: "imatge", "audio").
        Returns:
            Optional[Dict[str, Any]]: El diccionari de l'entrada de l'historial o None si no es troba.
        """
        history_to_search = self.get_capture_history(content_type_filter)
        if not history_to_search:
            # print(f"[FileManager ({self._default_prefix}) WARNING]: Historial buit (filtre: {content_type_filter}).")
            return None

        if isinstance(identifier, str): # Cerca per nom de fitxer
            for entry in reversed(history_to_search): # Cerca des del més recent
                if entry.get("filename") == identifier:
                    return entry
            # print(f"[FileManager ({self._default_prefix}) WARNING]: Fitxer '{identifier}' no trobat a l'historial (filtre: {content_type_filter}).")
            return None
        elif isinstance(identifier, int): # Cerca per índex
            try:
                return history_to_search[identifier]
            except IndexError:
                # print(f"[FileManager ({self._default_prefix}) WARNING]: Índex {identifier} fora de rang (mida: {len(history_to_search)}, filtre: {content_type_filter}).")
                return None
        else:
            print(f"[FileManager ({self._default_prefix}) ERROR]: Identificador '{identifier}' no vàlid. Ha de ser string o int.")
            return None
            
    def clear_history(self):
        """
        Neteja l'historial de captures (tant en RAM com al disc).
        """
        self.capture_history = []
        self._save_history_to_disk() # Això crearà un fitxer JSON buit
        print(f"[FileManager ({self._default_prefix})]: Historial de captures netejat (RAM i disc).")

    def delete_capture_file(self, identifier_or_filepath: Union[str, int], content_type_filter: Optional[str] = None) -> bool:
        """
        Elimina un fitxer de captura del disc i de l'historial.
        Args:
            identifier_or_filepath (Union[str, int]): La ruta completa del fitxer, el seu nom de fitxer, o l'índex a l'historial.
            content_type_filter (Optional[str]): Filtra per tipus de contingut si s'usa un identificador no de ruta.
        Returns:
            bool: True si el fitxer s'ha eliminat amb èxit, False altrament.
        """
        entry_to_delete: Optional[Dict[str, Any]] = None
        actual_filepath_to_delete = None

        if isinstance(identifier_or_filepath, str) and os.path.isabs(identifier_or_filepath):
            # Si és una ruta absoluta, la utilitzem directament i busquem l'entrada a l'historial
            actual_filepath_to_delete = identifier_or_filepath
            for entry in self.capture_history:
                if entry.get("filepath") == actual_filepath_to_delete:
                    entry_to_delete = entry
                    break
        else:
            # Si és un nom de fitxer o un índex, busquem l'entrada a l'historial
            entry_to_delete = self.get_capture_entry_by_identifier(identifier_or_filepath, content_type_filter)
            if entry_to_delete:
                actual_filepath_to_delete = entry_to_delete.get("filepath")

        if not actual_filepath_to_delete:
            print(f"[FileManager ({self._default_prefix}) WARNING]: No s'ha trobat cap fitxer o entrada d'historial per eliminar amb identificador '{identifier_or_filepath}'.")
            return False

        file_removed_from_disk = False
        if os.path.exists(actual_filepath_to_delete):
            try:
                os.remove(actual_filepath_to_delete)
                file_removed_from_disk = True
                print(f"[FileManager ({self._default_prefix})]: Fitxer '{os.path.basename(actual_filepath_to_delete)}' eliminat del disc.")
            except OSError as e:
                print(f"[FileManager ({self._default_prefix}) ERROR]: Eliminant '{actual_filepath_to_delete}' del disc: {e}")
                return False # No s'ha pogut eliminar del disc
        else: # El fitxer ja no existia al disc
            file_removed_from_disk = True
            print(f"[FileManager ({self._default_prefix})]: Fitxer '{os.path.basename(actual_filepath_to_delete)}' no trobat al disc (ja eliminat o mai va existir).")

        # Eliminar l'entrada de l'historial si es va trobar
        if entry_to_delete and entry_to_delete in self.capture_history:
            self.capture_history.remove(entry_to_delete)
            self._save_history_to_disk() # Guarda l'historial actualitzat
            print(f"[FileManager ({self._default_prefix})]: Entrada per '{os.path.basename(actual_filepath_to_delete)}' eliminada de l'historial.")
        elif file_removed_from_disk: # S'ha eliminat del disc, però no estava a l'historial actual
            print(f"[FileManager ({self._default_prefix})]: Fitxer '{os.path.basename(actual_filepath_to_delete)}' eliminat del disc (no estava a l'historial actual).")
            
        return file_removed_from_disk
