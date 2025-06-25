import os
import sys
import shutil
import time
import json

# --- Configuración para la nueva estructura de proyecto ---
# Definimos el directorio raíz del proyecto dinámicamente.
# Esto asume que el script de pruebas está en 'el_meu_projecte/tests/'
# y que los módulos a importar están en 'el_meu_projecte/scripts/'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DADES_DIR = os.path.join(PROJECT_ROOT, "data") # Asumimos 'data' en la raíz del proyecto para los datos

# Ya no necesitamos crear archivos temporales, ya que asumimos que existen.
# Las variables FILE_MANAGER_CODE, MICROPHONE_CODE, CAMERA_CODE, ALTAVEU_CODE
# ya no son necesarias aquí.

# Las funciones setup_test_environment y cleanup_test_environment
# ya no son necesarias para crear los archivos de módulos.
# Sin embargo, podemos mantener una versión simplificada para gestionar el directorio de DADES.

def setup_test_environment_simplified():
    print("--- CONFIGURANT ENTORN DE PROVES (Simplificat) ---")
    # Aseguramos que el directorio 'data' exista para las capturas
    os.makedirs(DADES_DIR, exist_ok=True)
    print(f"Directori de dades '{DADES_DIR}' assegurat.")
    # Si quieres un directorio base_directory_path específico para las pruebas dentro de 'data'
    # puedes crearlo aquí o dejar que FileManager lo cree.
    print("--- ENTORN DE PROVES CONFIGURAT ---\n")

def cleanup_test_environment_simplified():
    print("\n--- NETEJANT ENTORN DE PROVES (Simplificat) ---")
    # Puedes optar por limpiar solo los subdirectorios de capturas creados por FileManager,
    # en lugar de todo el TEST_ROOT_DIR, que ya no existe como tal.
    # Por ejemplo, si FileManager crea 'test_captures_v2' y 'altres_captures_test_v2' dentro de 'data'.
    try:
        # Esto eliminará el contenido de los directorios de captura específicos creados durante el test.
        # Ajusta según cómo quieras gestionar la limpieza.
        test_captures_path = os.path.join(DADES_DIR, "test_captures_v2")
        altres_captures_path = os.path.join(DADES_DIR, "altres_captures_test_v2")
        final_del_test_path = os.path.join(DADES_DIR, "final_del_test_dir_v2")

        if os.path.exists(test_captures_path):
            shutil.rmtree(test_captures_path)
            print(f"Directori '{test_captures_path}' eliminat.")
        if os.path.exists(altres_captures_path):
            shutil.rmtree(altres_captures_path)
            print(f"Directori '{altres_captures_path}' eliminat.")
        if os.path.exists(final_del_test_path):
            shutil.rmtree(final_del_test_path)
            print(f"Directori '{final_del_test_path}' eliminat.")

    except Exception as e:
        print(f"Error netejant directoris de proves dins de '{DADES_DIR}': {e}")
    print("--- NETEJA FINALITZADA ---")


def run_tests(nom_carpeta_moduls: str = "dispositius"): # Añadimos un parámetro para el nombre de la carpeta
    print("--- INICIANT PROVES DE FILEMANAGER ---")
    original_sys_path = list(sys.path)

    # --- Càrrega del directori arrel del projecte al sys.path ---
    # Això és crucial perquè Python trobi els paquets 'scripts' i 'data'.
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    print(f"'{PROJECT_ROOT}' afegit a sys.path per a imports.")
    # --- Fi de la càrrega ---

    try:
        # --- Imports de les teves classes ---
        # Ara els imports són absoluts des de la 'arrel del projecte'
        from scripts.FileManager import FileManager
        from scripts import controladors # Importamos el paquete para acceder a los módulos dentro

        # Accedemos a las clases a través del paquete
        # Asegúrate de que <nom_carpeta> és el nom real del teu directori (per exemple, 'dispositius')
        from scripts.controladors.Camera import Camera
        from scripts.controladors.Microphone import Microphone
        from scripts.controladors.Altaveu import Altaveu
        
        # --- Fi dels imports ---

        print("\n[TEST 1]: Inicialització de FileManager")
        fm = FileManager(default_prefix="test_run", base_directory="test_captures_v2")
        # fm._project_root ahora debe apuntar a la raíz de tu proyecto, no al TEST_ROOT_DIR temporal.
        assert fm._project_root == PROJECT_ROOT
        # La base_directory_path ahora debe estar dentro de tu DADES_DIR real
        expected_base_dir = os.path.join(DADES_DIR, "test_captures_v2")
        assert fm._base_directory_path == expected_base_dir
        assert os.path.exists(expected_base_dir)
        print("[TEST 1]: PASSAT - FileManager inicialitzat.")

        print("\n[TEST 2]: Registre de Maquinari")
        cam = Camera(resolucio=(320,240))
        mic = Microphone(samplerate=16000)
        spk = Altaveu()

        fm.register_camera(cam)
        assert fm._camera is cam
        fm.register_microphone(mic)
        assert fm._microphone is mic
        fm.register_speaker(spk)
        assert fm._speaker is spk
        print("[TEST 2]: PASSAT - Maquinari registrat.")

        photo_path = None
        photo_filename = None
        audio_path = None
        audio_filename = None

        with cam:
            print(f"\n[INFO] Estat de la càmera dins del 'with': activa={cam.get_camera_status()}, simulada={cam._is_real_camera_simulated}")

            print("\n[TEST 3]: Captura de Foto")
            photo_path = fm.take_photo()
            assert photo_path is not None, "take_photo() ha retornat None."
            assert os.path.exists(photo_path), f"Fitxer foto '{photo_path}' no existeix."
            assert "imatge" in os.path.basename(photo_path)
            assert fm.get_capture_history(content_type_filter="imatge")
            print(f"Foto guardada a: {photo_path}")
            print("[TEST 3]: PASSAT - Captura de foto.")
            photo_filename = os.path.basename(photo_path)

            print("\n[TEST 4]: Gravació d'Àudio")
            audio_path = fm.record_audio(duration=1)
            if audio_path:
                assert os.path.exists(audio_path), f"Fitxer àudio '{audio_path}' no existeix."
                assert "audio" in os.path.basename(audio_path)
                assert fm.get_capture_history(content_type_filter="audio")
                print(f"Àudio guardat a: {audio_path}")
                print("[TEST 4]: PASSAT - Gravació d'àudio.")
                audio_filename = os.path.basename(audio_path)
            else:
                print("[TEST 4]: FALLAT/SALTAT - record_audio() retornà None. Comprova config sounddevice/mic.")

        print(f"\n[INFO] Estat de la càmera fora del 'with': activa={cam.get_camera_status()}")

        print("\n[TEST 5]: Obtenció d'Historial i Entrades")
        history = fm.get_capture_history()
        expected_entries = (1 if photo_path else 0) + (1 if audio_path else 0)
        assert len(history) == expected_entries, f"Historial hauria de tenir {expected_entries} entrades, té {len(history)}."

        if photo_path:
            entry_by_idx_img = fm.get_capture_entry_by_identifier(0)
            assert entry_by_idx_img and entry_by_idx_img["content_type"] == "imatge"
            entry_by_name_img = fm.get_capture_entry_by_identifier(photo_filename)
            assert entry_by_name_img and entry_by_name_img["filename"] == photo_filename

        if audio_path:
            audio_idx = 0 if not photo_path else 1
            entry_by_idx_audio = fm.get_capture_entry_by_identifier(audio_idx)
            assert entry_by_idx_audio and entry_by_idx_audio["content_type"] == "audio"
            entry_by_name_audio = fm.get_capture_entry_by_identifier(audio_filename)
            assert entry_by_name_audio and entry_by_name_audio["filename"] == audio_filename
        print(f"Historial actual ({len(history)} entrades).")
        print("[TEST 5]: PASSAT - Gestió d'historial.")

        print("\n[TEST 6]: Reproducció d'Àudio (simulada/real depenent d'aplay)")
        if audio_path:
            played = fm.play_audio_from_history(audio_filename)
            print(f"Resultat de play_audio_from_history per nom: {played}")
            audio_idx = 0 if not photo_path else 1
            played_idx = fm.play_audio_from_history(audio_idx)
            print(f"Resultat de play_audio_from_history per índex: {played_idx}")
            print("[TEST 6]: PASSAT (executat) - Reproducció d'àudio.")
        else:
            print("\n[TEST 6]: Reproducció d'Àudio - SALTAT (àudio no gravat).")

        print("\n[TEST 7]: Canvi de Directori Base")
        old_history_file = fm._history_filename
        with cam:
            fm.set_base_directory("altres_captures_test_v2")
            new_base_dir = os.path.join(DADES_DIR, "altres_captures_test_v2") # Apunta a DADES_DIR
            assert fm._base_directory_path == new_base_dir
            assert os.path.exists(new_base_dir)
            assert len(fm.get_capture_history()) == 0
            assert os.path.exists(old_history_file)

            new_photo_path = fm.take_photo()
            assert new_photo_path and os.path.dirname(new_photo_path) == new_base_dir
            assert len(fm.get_capture_history()) == 1
            print(f"Nova foto en nou directori: {new_photo_path}")
        print("[TEST 7]: PASSAT - Canvi de directori base.")

        print("\n[TEST 8]: Eliminació de Fitxer")
        fm.set_base_directory("test_captures_v2")
        original_history_len = len(fm.get_capture_history())

        if photo_path:
            deleted = fm.delete_capture_file(photo_filename)
            assert deleted, f"Error eliminant '{photo_filename}'."
            assert not os.path.exists(photo_path), f"Fitxer '{photo_path}' encara existeix."
            assert len(fm.get_capture_history()) == original_history_len - 1
            print(f"Fitxer '{photo_filename}' eliminat.")
        else:
            print(f"SALTANT eliminació de '{photo_filename}' perquè no es va crear.")

        deleted_non_existent_idx = fm.delete_capture_file(999)
        assert not deleted_non_existent_idx
        deleted_non_existent_name = fm.delete_capture_file("fitxer_inventat.jpg")
        assert not deleted_non_existent_name
        print("[TEST 8]: PASSAT - Eliminació de fitxer.")

        print("\n[TEST 9]: Neteja d'Historial")
        fm.clear_history()
        assert len(fm.get_capture_history()) == 0
        history_file_path = fm._history_filename
        with open(history_file_path, 'r') as hf:
            content = json.load(hf)
            assert isinstance(content, list) and len(content) == 0
        print("[TEST 9]: PASSAT - Neteja d'historial.")

        print("\n[TEST 10]: Prova de __del__ (guardat d'historial)")
        fm_final_test_instance = FileManager(default_prefix="final_test", base_directory="final_del_test_dir_v2")
        cam_final = Camera(nom_camera="FinalCam", resolucio=(100,100))
        fm_final_test_instance.register_camera(cam_final)

        with cam_final:
            fm_final_test_instance.take_photo()

        hist_file_final = fm_final_test_instance._history_filename
        num_entries_before_del = len(fm_final_test_instance.capture_history)
        assert num_entries_before_del > 0

        del fm_final_test_instance

        assert os.path.exists(hist_file_final)
        fm_check_del = FileManager(default_prefix="check_del", base_directory="final_del_test_dir_v2")
        assert len(fm_check_del.capture_history) == num_entries_before_del
        print(f"Historial després de __del__ conté {len(fm_check_del.capture_history)} entrades (esperat: {num_entries_before_del}).")
        del fm_check_del
        del cam_final

        print("[TEST 10]: PASSAT - __del__ va guardar l'historial.")


        print("\n--- TOTES LES PROVES HAN FINALITZAT AMB ÈXIT (O AMB AVISOS) ---")

    except ImportError as e:
        print(f"\nERROR D'IMPORTACIÓ: {e}")
        print("Assegura't que el teu 'PYTHONPATH' inclou el directori 'el_meu_projecte' o que executes el test des de l'arrel del projecte.")
        print(f"També, verifica que els mòduls '{e.name}' existeixen a les rutes esperades: 'scripts/' o 'scripts/<nom_carpeta>/'.")
        import traceback
        traceback.print_exc()
    except AssertionError as e:
        print(f"\n!!! FALLADA DE TEST: {e} !!!")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n!!! ERROR INESPERAT DURANT LES PROVES: {e} !!!")
        import traceback
        traceback.print_exc()
    finally:
        sys.path = original_sys_path
        print("Restaurat sys.path original.")


if __name__ == "__main__":
    # Defineix el nom de la carpeta que conté 'camera.py', 'microphone.py', 'altaveu.py'
    # Substitueix '<nom_carpeta>' pel nom real (p. ex., 'dispositius' o 'hardware')
    NOM_CARPETA_MODULS = "dispositius" # <-- CANVIA AQUEST NOM DE CARPETA SEGONS EL TEU PROJECTE!

    setup_test_environment_simplified()
    try:
        run_tests(nom_carpeta_moduls=NOM_CARPETA_MODULS)
    finally:
        # input("Prem Enter per netejar l'entorn de proves...")
        cleanup_test_environment_simplified()
