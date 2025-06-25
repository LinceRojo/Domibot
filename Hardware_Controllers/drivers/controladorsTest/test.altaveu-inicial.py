import os
import shutil
import numpy as np
import soundfile as sf
import time # Afegim time per pausar si és necessari

# Importem la classe Altaveu des de la seva ubicació al paquet
# Assegura't que aquesta ruta sigui correcta segons la teva estructura de carpetes
from scripts.controladors.Altaveu import Altaveu

def run_altaveu_test():
    """
    Funció principal per executar el test de la classe Altaveu.
    """
    print("--- Iniciant Test de la Classe Altaveu ---")

    # --- Configuració de l'estructura de fitxers de prova ---
    # Creem directoris temporals per a les proves
    PROJECT_ROOT_NAME = "ProjecteMultimediaTest_Altaveu"
    SCRIPTS_FOLDER = "programes" # Carpeta simulada per scripts
    DATA_FOLDER = "dades_media"  # Carpeta simulada per dades
    AUDIO_TEST_DIR = "audio_test_files" # Subcarpeta per als fitxers d'àudio de test

    # Construïm les rutes absolutes per als directoris de prova
    # Aquest test s'executa des de ~/DominoScara, així que creem la carpeta de prova aquí
    project_root_for_test = os.path.abspath(os.path.join(os.getcwd(), PROJECT_ROOT_NAME))
    scripts_dir_for_test = os.path.join(project_root_for_test, SCRIPTS_FOLDER)
    data_dir_for_test = os.path.join(project_root_for_test, DATA_FOLDER)
    audio_output_dir = os.path.join(data_dir_for_test, AUDIO_TEST_DIR)

    # Neteja prèvia: si els directoris de prova ja existeixen, els eliminem
    if os.path.exists(project_root_for_test):
        print(f"Directori de prova existent '{project_root_for_test}' detectat. Netejant...")
        shutil.rmtree(project_root_for_test)

    # Creem els directoris necessaris
    os.makedirs(scripts_dir_for_test, exist_ok=True)
    os.makedirs(audio_output_dir, exist_ok=True)
    print(f"Estructura de directoris de prova creada a: {project_root_for_test}")

    # --- Creació d'un fitxer d'àudio de prova ---
    test_audio_filepath = os.path.join(audio_output_dir, "test_sound.wav")
    samplerate_test = 44100  # Mostres per segon (qualitat CD)
    duration_test = 2        # Durada en segons
    frequency_test = 440     # Freqüència de l'ona (Hz, La central)

    # Generem dades d'àudio d'una ona sinusoïdal simple
    t = np.linspace(0., duration_test, int(samplerate_test * duration_test), endpoint=False)
    audio_data_test = 0.5 * np.sin(2. * np.pi * frequency_test * t) # Amplitud 0.5

    # Guardem les dades en un fitxer WAV
    try:
        sf.write(test_audio_filepath, audio_data_test, samplerate_test)
        print(f"Fitxer d'àudio de prova '{test_audio_filepath}' creat correctament.")
    except Exception as e:
        print(f"ERROR: No s'ha pogut crear el fitxer d'àudio de prova: {e}")
        # Aquí pots optar per sortir o continuar el test amb limitacions
        clean_up(project_root_for_test) # Neteja abans de sortir
        return

    # --- Simulació de canvi de directori de treball ---
    # Canviem el directori de treball per assegurar-nos que el codi gestiona rutes absolutes
    execution_dir_for_test = os.path.abspath(os.path.join(os.getcwd(), "execucions_test_altaveu"))
    if os.path.exists(execution_dir_for_test):
        shutil.rmtree(execution_dir_for_test)
    os.makedirs(execution_dir_for_test, exist_ok=True)

    original_cwd = os.getcwd() # Guardem el directori original
    os.chdir(execution_dir_for_test) # Canviem al directori de simulació
    print(f"\n--- Canviat el directori de treball a: {os.getcwd()} ---")

    # --- Test de la Classe Altaveu ---
    try:
        # 1. Test de llistat de dispositius
        print("\n--- Test de llistat de dispositius d'àudio (sounddevice) ---")
        # Instanciem l'altaveu només per llistar, sense un dispositiu específic
        with Altaveu(nom_altaveu="AltaveuLlistador") as list_spk:
            list_spk.list_output_devices(tool="sounddevice")
            list_spk.list_output_devices(tool="aplay") # També provar aplay

        # 2. Test de reproducció d'àudio
        print("\n--- Test de reproducció d'àudio amb Altaveu ---")
        # Creem una instància d'Altaveu, utilitzant 'device_label_alsa=None' per al dispositiu per defecte
        with Altaveu(nom_altaveu="Altaveu Principal", device_label_alsa=None) as spk:
            print("\n--- Intentant reproduir un fitxer d'àudio existent (blocant) ---")
            success = spk.play_audio_file(test_audio_filepath, blocking=True)
            if success:
                print("Reproducció del fitxer de prova finalitzada amb èxit.")
            else:
                print("La reproducció del fitxer de prova ha fallat. Revisa els errors anteriors.")

            # Prova de reproducció no blocant (en background)
            print("\n--- Intentant reproduir el mateix fitxer (no blocant) ---")
            success_non_blocking = spk.play_audio_file(test_audio_filepath, blocking=False)
            if success_non_blocking:
                print("Reproducció no blocant iniciada. Esperant 3 segons abans de continuar...")
                time.sleep(3) # Donem temps a que es reprodueixi una part
                print("Continuant amb el test.")
            else:
                print("La reproducció no blocant ha fallat.")

            # 3. Test de reproducció d'un fitxer inexistent
            print("\n--- Intentant reproduir un fitxer inexistent ---")
            spk.play_audio_file("non_existent_file.wav")
            print("Esperat: Missatge d'error indicant que el fitxer no existeix.")

    except Exception as e:
        print(f"\nS'ha produït un ERROR CRÍTIC durant el test de l'altaveu: {e}")
    finally:
        # --- Neteja final ---
        os.chdir(original_cwd) # Tornem al directori original
        print(f"\n--- Test de l'Altaveu Finalitzat. Tornat al directori original: {os.getcwd()} ---")
        clean_up(project_root_for_test)
        clean_up(execution_dir_for_test)
        print("Tots els directoris i fitxers de prova han estat netejats.")

def clean_up(path):
    """Funció auxiliar per netejar directoris."""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"Directori de prova '{path}' netejat.")
        except OSError as e:
            print(f"Error en netejar el directori '{path}': {e}")


# Quan s'executa el script directament, cridem la funció de test
if __name__ == "__main__":
    run_altaveu_test()
