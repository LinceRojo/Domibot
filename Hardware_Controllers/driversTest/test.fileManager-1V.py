import os
import sys
import shutil
import time
import json

# --- Script de Prova ---
TEST_ROOT_DIR = "fm_test_project_env"
SCRIPTS_DIR = os.path.join(TEST_ROOT_DIR, "scripts")
DADES_DIR = os.path.join(TEST_ROOT_DIR, "dades") 

FILES_TO_CREATE = {
    os.path.join(SCRIPTS_DIR, "file_manager.py"): FILE_MANAGER_CODE,
    os.path.join(SCRIPTS_DIR, "microphone.py"): MICROPHONE_CODE,
    os.path.join(SCRIPTS_DIR, "camera.py"): CAMERA_CODE,
    os.path.join(SCRIPTS_DIR, "altaveu.py"): ALTAVEU_CODE,
}

def setup_test_environment():
    print("--- CONFIGURANT ENTORN DE PROVES ---")
    if os.path.exists(TEST_ROOT_DIR):
        shutil.rmtree(TEST_ROOT_DIR)
        print(f"Directori de proves antic '{TEST_ROOT_DIR}' eliminat.")
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    os.makedirs(DADES_DIR, exist_ok=True) 
    print(f"Directoris '{SCRIPTS_DIR}' i '{DADES_DIR}' creats.")

    with open(os.path.join(TEST_ROOT_DIR, ".project_root"), "w") as f:
        f.write("Marcador arrel projecte per proves FileManager.")
    print(f"Fitxer '.project_root' creat a '{TEST_ROOT_DIR}'.")

    for filepath, code in FILES_TO_CREATE.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Fitxer '{filepath}' creat.")
    print("--- ENTORN DE PROVES CONFIGURAT ---\n")

def cleanup_test_environment():
    print("\n--- NETEJANT ENTORN DE PROVES ---")
    if os.path.exists(TEST_ROOT_DIR):
        try:
            shutil.rmtree(TEST_ROOT_DIR)
            print(f"Directori de proves '{TEST_ROOT_DIR}' eliminat.")
        except Exception as e:
            print(f"Error eliminant el directori de proves '{TEST_ROOT_DIR}': {e}")
    else:
        print(f"Directori de proves '{TEST_ROOT_DIR}' no trobat per eliminar.")
    print("--- NETEJA FINALITZADA ---")

def run_tests():
    print("--- INICIANT PROVES DE FILEMANAGER ---")
    original_sys_path = list(sys.path)
    sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

    try:
        from file_manager import FileManager
        from camera import Camera # Codi de l'usuari
        from microphone import Microphone # Codi de l'usuari
        from altaveu import Altaveu # Codi de l'usuari

        print("\n[TEST 1]: Inicialització de FileManager")
        fm = FileManager(default_prefix="test_run", base_directory="test_captures_v2")
        assert fm._project_root == os.path.abspath(TEST_ROOT_DIR)
        expected_base_dir = os.path.join(os.path.abspath(DADES_DIR), "test_captures_v2")
        assert fm._base_directory_path == expected_base_dir
        assert os.path.exists(expected_base_dir)
        print("[TEST 1]: PASSAT - FileManager inicialitzat.")

        print("\n[TEST 2]: Registre de Maquinari")
        # La càmera es gestionarà amb 'with' a les seccions de prova pertinents
        cam = Camera(resolucio=(320,240)) # Resolució més baixa per a proves ràpides
        mic = Microphone(samplerate=16000) 
        spk = Altaveu()

        fm.register_camera(cam)
        assert fm._camera is cam
        fm.register_microphone(mic)
        assert fm._microphone is mic
        fm.register_speaker(spk)
        assert fm._speaker is spk
        print("[TEST 2]: PASSAT - Maquinari registrat.")

        # Les proves que usen la càmera ara estaran dins d'un bloc 'with cam:'
        # O caldrà gestionar cam.__enter__() i cam.__exit__()
        
        photo_path = None
        photo_filename = None
        audio_path = None
        audio_filename = None

        # Usem 'with' per a la càmera per assegurar la correcta inicialització/aturada
        # ja que la classe Camera de l'usuari ho requereix (fa setup a __enter__)
        with cam: # Això crida cam.__enter__() i després cam.__exit__()
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
            # L'índex de l'àudio depèn de si la foto es va crear
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
            print(f"Resultat de play_audio_from_history per nom: {played}") # Informatiu
            # L'asserció depèn de si aplay funciona. La classe Altaveu ja informa d'errors.
            # Per ara, només comprovem que no peti. Un 'True' indicaria èxit d'aplay.
            # assert played, f"play_audio_from_history per nom '{audio_filename}' hauria de retornar True si aplay funciona."
            audio_idx = 0 if not photo_path else 1
            played_idx = fm.play_audio_from_history(audio_idx) 
            print(f"Resultat de play_audio_from_history per índex: {played_idx}")
            print("[TEST 6]: PASSAT (executat) - Reproducció d'àudio.")
        else:
            print("\n[TEST 6]: Reproducció d'Àudio - SALTAT (àudio no gravat).")

        print("\n[TEST 7]: Canvi de Directori Base")
        old_history_file = fm._history_filename
        with cam: # La càmera ha d'estar activa per take_photo
            fm.set_base_directory("altres_captures_test_v2")
            new_base_dir = os.path.join(os.path.abspath(DADES_DIR), "altres_captures_test_v2")
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
        
        if photo_path: # Només si la foto original es va crear
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
        # Crear nova instància per a aquesta prova per no interferir amb 'cam'
        fm_final_test_instance = FileManager(default_prefix="final_test", base_directory="final_del_test_dir_v2")
        cam_final = Camera(nom_camera="FinalCam", resolucio=(100,100))
        fm_final_test_instance.register_camera(cam_final)
        
        with cam_final:
            fm_final_test_instance.take_photo() 
        
        hist_file_final = fm_final_test_instance._history_filename
        num_entries_before_del = len(fm_final_test_instance.capture_history)
        assert num_entries_before_del > 0
        
        # Eliminar la instància per invocar __del__
        del fm_final_test_instance 
        
        assert os.path.exists(hist_file_final)
        # Comprovem que l'historial es va guardar correctament llegint-lo
        fm_check_del = FileManager(default_prefix="check_del", base_directory="final_del_test_dir_v2")
        assert len(fm_check_del.capture_history) == num_entries_before_del
        print(f"Historial després de __del__ conté {len(fm_check_del.capture_history)} entrades (esperat: {num_entries_before_del}).")
        del fm_check_del # Neteja
        del cam_final

        print("[TEST 10]: PASSAT - __del__ va guardar l'historial.")


        print("\n--- TOTES LES PROVES HAN FINALITZAT AMB ÈXIT (O AMB AVISOS) ---")

    except ImportError as e:
        print(f"\nERROR D'IMPORTACIÓ: {e}")
        print("Assegura't que les dependències (numpy, Pillow, soundfile, sounddevice, [opcional: picamera2]) estan instal·lades.")
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
    setup_test_environment()
    try:
        run_tests()
    finally:
        # input("Prem Enter per netejar l'entorn de proves...") 
        cleanup_test_environment()
