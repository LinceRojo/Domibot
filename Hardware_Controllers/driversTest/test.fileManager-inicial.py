from scripts.controladors.Altaveu import Altaveu
from scripts.controladors.Camera import Camera
from scripts.controladors.Microphone import Microphone
from scripts.FileManager import FileManager
import os
import shutil
import time
import json
import numpy as np
from PIL import Image
import soundfile as sf
import sounddevice as sd
import subprocess # Per a la classe Altaveu

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Union, Dict


# =======================================================================================
# LÒGICA PRINCIPAL DE LA PROVA
# =======================================================================================

# --- Configuració del test ---
TEST_ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_temp_real_data")
TEST_DATA_FOLDER_NAME = "real_data"
TEST_CAPTURES_SUBDIR = "real_captures"
TEST_SCRIPTS_FOLDER_NAME = "real_scripts"

PROJECT_ROOT_MARKER_PATH = os.path.join(TEST_ROOT_DIR, FileManager.PROJECT_ROOT_MARKER_FILENAME)
DUMMY_SCRIPTS_PATH = os.path.join(TEST_ROOT_DIR, TEST_SCRIPTS_FOLDER_NAME)

def setup_test_environment():
    """Prepara l'entorn de directoris per a la prova."""
    if os.path.exists(TEST_ROOT_DIR):
        shutil.rmtree(TEST_ROOT_DIR)
    os.makedirs(TEST_ROOT_DIR)
    os.makedirs(DUMMY_SCRIPTS_PATH)
    with open(PROJECT_ROOT_MARKER_PATH, "w") as f:
        f.write("This is a test project root marker for real hardware.")
    print(f"\n--- Entorn de prova real preparat a '{TEST_ROOT_DIR}' ---")

def cleanup_test_environment():
    """Neteja l'entorn de directoris després de la prova."""
    if os.path.exists(TEST_ROOT_DIR):
        shutil.rmtree(TEST_ROOT_DIR)
    print(f"\n--- Entorn de prova real netejat de '{TEST_ROOT_DIR}' ---")

# --- Funció principal de prova ---
def run_file_manager_real_tests():
    """Executa la bateria de proves per a FileManager amb hardware real."""
    setup_test_environment()
    file_manager = None
    camera_instance = None
    mic_instance = None
    speaker_instance = None

    try:
        print("\n=======================================================")
        print("    Iniciant Prova REAL de la Classe FileManager (Hardware)")
        print("=======================================================")

        # --- Prova 1: Inicialització de FileManager i Creació de Directoris ---
        print("\n--- Prova 1: Inicialització de FileManager i Creació de Directoris ---")
        original_cwd = os.getcwd()
        os.chdir(DUMMY_SCRIPTS_PATH)
        
        file_manager = FileManager(
            base_directory=TEST_CAPTURES_SUBDIR,
            default_prefix="real_robot",
            scripts_folder_name=TEST_SCRIPTS_FOLDER_NAME,
            data_folder_name=TEST_DATA_FOLDER_NAME
        )
        expected_base_path = os.path.join(TEST_ROOT_DIR, TEST_DATA_FOLDER_NAME, TEST_CAPTURES_SUBDIR)
        assert file_manager._base_directory_path == expected_base_path
        assert os.path.exists(expected_base_path)
        print(f"RESULTAT: Inicialització i creació de directoris OK. Base: '{file_manager._base_directory_path}'")
        os.chdir(original_cwd)

        # --- Prova 2: Registre de Components Reals ---
        print("\n--- Prova 2: Registre de Components Reals ---")
        
        # Instanciem les classes de hardware i les activem manualment
        camera_instance = Camera(nom_camera="CameraPrincipal", resolucio=(640, 480))
        camera_instance.__enter__() # Activa la càmera
        file_manager.register_camera(camera_instance)
        assert file_manager._camera is not None
        if camera_instance.get_camera_status():
            print(f"RESULTAT: Càmera '{camera_instance.nom}' registrada i activa (mode: {'REAL' if not camera_instance._is_real_camera_simulated else 'SIMULAT'}).")
        else:
            print(f"ADVERTENCIA: Càmera '{camera_instance.nom}' registrada, però no activa (mode: {'REAL' if not camera_instance._is_real_camera_simulated else 'SIMULAT'}). Les proves de càmera es saltaran.")
        
        mic_instance = Microphone(nom_microfon="MicPrincipal", samplerate=44100, channels=1)
        mic_instance.__enter__() # Prepara el micròfon
        file_manager.register_microphone(mic_instance)
        assert file_manager._microphone is not None
        print(f"RESULTAT: Micròfon '{mic_instance.nom}' registrat.")
        
        speaker_instance = Altaveu(nom_altaveu="AltaveuPrincipal")
        speaker_instance.__enter__() # Prepara l'altaveu
        file_manager.register_speaker(speaker_instance)
        assert file_manager._speaker is not None
        print(f"RESULTAT: Altaveu '{speaker_instance.nom}' registrat.")
            
        print("RESULTAT: Intent de registre de components reals completat. Revisa els missatges anteriors per veure quins s'han registrat correctament.")


        # --- Prova 3: Captura d'Imatge (Si la càmera està operativa) ---
        if file_manager._camera and file_manager._camera.get_camera_status():
            print("\n--- Prova 3: Captura d'Imatge Real/Simulada ---")
            if file_manager._camera._is_real_camera_simulated:
                print("MODE SIMULAT: No es necessita intervenció física per a la càmera.")
            else:
                print("INSTRUCCIÓ: POSA'T DAVANT LA CÀMERA ARA PER A LA CAPTURA!")
            time.sleep(1)

            photo_filepath = file_manager.take_photo()
            assert photo_filepath is not None and os.path.exists(photo_filepath)
            print(f"RESULTAT: Imatge capturada i guardada a '{photo_filepath}' OK.")
            
            history = file_manager.get_capture_history(content_type_filter="imatge")
            assert len(history) == 1
            assert history[0]["filepath"] == os.path.abspath(photo_filepath)
            print("RESULTAT: Entrada d'imatge a l'historial OK.")
        else:
            print("\n--- Prova 3 Saltada: Càmera no registrada o no operativa. ---")


        # --- Prova 4: Gravació d'Àudio (Si el micròfon està registrat) ---
        if file_manager._microphone:
            print("\n--- Prova 4: Gravació d'Àudio Real ---")
            print("INSTRUCCIÓ: PARLA CLARAMENT AL MICRÒFON DURANT 3 SEGONS ARA!")
            time.sleep(1)
            audio_filepath = file_manager.record_audio(duration=3)
            assert audio_filepath is not None and os.path.exists(audio_filepath)
            print(f"RESULTAT: Àudio real gravat i guardat a '{audio_filepath}' OK.")

            history = file_manager.get_capture_history(content_type_filter="audio")
            assert len(history) == 1
            assert history[0]["filepath"] == os.path.abspath(audio_filepath)
            print("RESULTAT: Entrada d'àudio real a l'historial OK.")
        else:
            print("\n--- Prova 4 Saltada: Micròfon no registrat o no operatiu. ---")

        # --- Prova 5: Canvi de Directori Base ---
        print("\n--- Prova 5: Canvi de Directori Base ---")
        new_subdir = "new_real_captures"
        file_manager.set_base_directory(new_subdir)
        expected_new_base_path = os.path.join(TEST_ROOT_DIR, TEST_DATA_FOLDER_NAME, new_subdir)
        assert file_manager._base_directory_path == expected_new_base_path
        assert os.path.exists(expected_new_base_path)
        print(f"RESULTAT: Canvi de directori base a '{file_manager._base_directory_path}' OK.")
        assert len(file_manager.get_capture_history()) == 0
        print("RESULTAT: Historial resetat per al nou directori OK.")

        if file_manager._camera and file_manager._camera.get_camera_status():
            photo_filepath_new = file_manager.take_photo()
            assert photo_filepath_new is not None and os.path.exists(photo_filepath_new)
            print(f"RESULTAT: Nova imatge capturada al nou directori: '{photo_filepath_new}'.")
            history_new_dir = file_manager.get_capture_history(content_type_filter="imatge")
            assert len(history_new_dir) == 1
            print("RESULTAT: Nova entrada a l'historial del nou directori OK.")
        else:
            print("--- Prova 5 (captura nova) saltada: Càmera no registrada o no operativa. ---")

        # --- Prova 6: Cerca i Reproducció d'Àudio (Si l'altaveu i micròfon estan operatius) ---
        if file_manager._speaker and file_manager._microphone:
            print("\n--- Prova 6: Cerca i Reproducció d'Àudio Real ---")
            print("INSTRUCCIÓ: GRAVANT ÀUDIO CURT PER A LA REPRODUCCIÓ...")
            audio_for_playback_filepath = file_manager.record_audio(duration=2)
            assert audio_for_playback_filepath is not None
            
            print("INSTRUCCIÓ: REPRODUINT L'ÀUDIO GRAVAT ARA. ESCOLTA ATENTAMENT!")
            time.sleep(1)
            success_play_by_name = file_manager.play_audio_from_history(os.path.basename(audio_for_playback_filepath))
            assert success_play_by_name is True
            print(f"RESULTAT: Reproducció d'àudio per nom '{os.path.basename(audio_for_playback_filepath)}' OK.")

            audio_history_entries = file_manager.get_capture_history(content_type_filter="audio")
            assert len(audio_history_entries) > 0
            success_play_by_index = file_manager.play_audio_from_history(0)
            assert success_play_by_index is True
            print("RESULTAT: Reproducció d'àudio per índex OK.")
            
            success_play_non_existent = file_manager.play_audio_from_history("non_existent_audio.wav")
            assert success_play_non_existent is False
            print("RESULTAT: Reproducció d'àudio no existent gestionada correctament.")
        else:
            print("\n--- Prova 6 Saltada: Altaveu i/o micròfon no registrats o no operatius. ---")

        # --- Prova 7: Eliminació de Fitxers i Historial ---
        print("\n--- Prova 7: Eliminació de Fitxers i Historial ---")
        
        if 'photo_filepath' in locals() and photo_filepath and os.path.exists(photo_filepath):
            print(f"Intentant eliminar la foto del directori antic: '{photo_filepath}'")
            delete_success = file_manager.delete_capture_file(photo_filepath)
            assert delete_success is True
            assert not os.path.exists(photo_filepath)
            print("RESULTAT: Eliminació de fitxer per ruta absoluta OK.")
        else:
            print("--- Prova 7 (eliminació foto antiga) saltada: Foto no capturada o no existent. ---")


        if 'audio_for_playback_filepath' in locals() and audio_for_playback_filepath and os.path.exists(audio_for_playback_filepath):
            print(f"Intentant eliminar l'àudio del directori actual: '{os.path.basename(audio_for_playback_filepath)}'")
            delete_success_by_name = file_manager.delete_capture_file(os.path.basename(audio_for_playback_filepath), content_type_filter="audio")
            assert delete_success_by_name is True
            assert not os.path.exists(audio_for_playback_filepath)
            history_after_delete = file_manager.get_capture_history(content_type_filter="audio")
            assert len(history_after_delete) == 0
            print("RESULTAT: Eliminació de fitxer per nom i tipus de contingut OK.")
        else:
            print("--- Prova 7 (eliminació àudio nou) saltada: Àudio no gravat o no existent. ---")

        delete_non_existent = file_manager.delete_capture_file("fake_file.jpg")
        assert delete_non_existent is False
        print("RESULTAT: Eliminació de fitxer no existent gestionada correctament.")

        # --- Prova 8: Neteja d'Historial ---
        print("\n--- Prova 8: Neteja d'Historial ---")
        file_manager.clear_history()
        assert len(file_manager.get_capture_history()) == 0
        history_json_path = os.path.join(file_manager._base_directory_path, f"historial_{file_manager._default_prefix}.json")
        with open(history_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data == []
        print("RESULTAT: Historial netejat OK.")

        # --- Prova 9: Gestió d'Errors i Components No Registrats ---
        print("\n--- Prova 9: Gestió d'Errors i Components No Registrats (després de desregistrar-los) ---")
        file_manager._camera = None
        file_manager._microphone = None
        file_manager._speaker = None

        print("Simulant captura de foto sense càmera registrada...")
        error_photo = file_manager.take_photo()
        assert error_photo is None
        print("Simulant gravació d'àudio sense micròfon registrat...")
        error_audio = file_manager.record_audio()
        assert error_audio is None
        print("Simulant reproducció d'àudio sense altaveu registrat...")
        error_play = file_manager.play_audio_from_history("some_audio.wav")
        assert error_play is False
        print("RESULTAT: Gestió d'errors per components no registrats OK.")
        
        print("Simulant registre de càmera amb objecte invàlid...")
        try:
            file_manager.register_camera(object())
            assert False, "Error: Registre de càmera amb objecte invàlid no ha llançat ValueError."
        except ValueError as e:
            print(f"RESULTAT: Registre de càmera amb objecte invàlid llança ValueError: {e}")

        print("Simulant registre d'altaveu amb objecte invàlid (tipus incorrecte)...")
        try:
            file_manager.register_speaker(object())
            assert False, "Error: Registre d'altaveu amb objecte invàlid no ha llançat TypeError."
        except TypeError as e:
            print(f"RESULTAT: Registre d'altaveu amb objecte invàlid llança TypeError: {e}")
        except ValueError as e: # Per si l'objecte no compleix la signatura, ja que el TypeError és per tipus
            print(f"RESULTAT: Registre d'altaveu amb objecte invàlid llança ValueError (per mètode absent): {e}")


        print("Simulant canvi de directori amb nom buit...")
        try:
            file_manager.set_base_directory("")
            assert False, "Error: Canvi de directori amb nom buit no ha llançat ValueError."
        except ValueError as e:
            print(f"RESULTAT: Canvi de directori amb nom buit llança ValueError: {e}")


    except Exception as e:
        print(f"\nERROR INESPERAT DURANT LES PROVES: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n=======================================================")
        print("          Finalitzant Prova REAL de la Classe FileManager")
        print("=======================================================")
        if camera_instance:
            camera_instance.__exit__(None, None, None) # Assegurem que la càmera es tanca
        if mic_instance:
            mic_instance.__exit__(None, None, None) # Assegurem que el micròfon es tanca
        if speaker_instance:
            speaker_instance.__exit__(None, None, None) # Assegurem que l'altaveu es tanca
        
        if file_manager:
            print("[TestRunner]: L'objecte FileManager s'està destruint, l'historial es guardarà.")
        cleanup_test_environment()
        print("\n--- Proves REALS finalitzades ---")

# Executar les proves
if __name__ == "__main__":
    run_file_manager_real_tests()
