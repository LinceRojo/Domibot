import os
import shutil
import numpy as np
import time
# Per instal·lar Pillow (necessari per guardar PNG/JPG):
# pip install Pillow
from PIL import Image

# Importem la classe Camera des de la seva ubicació al paquet
from scripts.controladors.Camera import Camera

# --- Configuració global del test ---
TEST_ROOT_DIR_CAM = "CameraInteractiveTestEnv"
CAPTURE_SUBDIR = "captures"

def run_interactive_camera_test():
    """
    Funció principal per executar el test interactiu de la classe Camera.
    """
    print("--- Iniciant Test Interactiu de la Classe Camera ---")

    test_env_path = os.path.abspath(os.path.join(os.getcwd(), TEST_ROOT_DIR_CAM))
    capture_path = os.path.join(test_env_path, CAPTURE_SUBDIR)

    original_cwd = os.getcwd() # Guardem el directori original

    try:
        # --- Preparació de l'entorn de test ---
        # Neteja prèvia i creació de directoris
        print(f"Preparant directori de prova a: {test_env_path}")
        if os.path.exists(test_env_path):
            shutil.rmtree(test_env_path) # Neteja total de l'entorn anterior
        os.makedirs(capture_path, exist_ok=True)
        print(f"Directori de captures creat a: {capture_path}")

        os.chdir(test_env_path) # Canviem al directori de test per aïllament
        print(f"\n--- Canviat el directori de treball a: {os.getcwd()} ---")

        # --- Test de la Classe Camera ---
        print("\n--- 1. Test d'inicialització i captura interactiva ---")
        with Camera(nom_camera="Càmera Interactiva", resolucio=(640, 480), default_extension="jpg") as cam:
            print(f"Estat de la càmera al context: {cam.get_camera_status()}")
            time.sleep(1) # Donem temps per inicialitzar

            print("\nCapturant una imatge per a verificació manual...")
            image_data, extension, metadata = cam.capture_image_data()

            if image_data is not None:
                # Construïm la ruta completa per desar la imatge
                timestamp = int(time.time())
                filename = f"capture_{timestamp}.{extension}"
                full_image_path = os.path.join(capture_path, filename)

                # Desem la imatge utilitzant Pillow
                try:
                    img = Image.fromarray(image_data)
                    img.save(full_image_path)
                    print(f"\nIMATGE CREADA PER A LA TEVA REVISIÓ:")
                    print(f"Ruta: {full_image_path}")
                    print(f"Mida de la imatge (pixels): {image_data.shape[1]}x{image_data.shape[0]}")
                    print(f"Format: .{extension}")

                    # --- PART INTERACTIVA ---
                    print("\nSi us plau, ara pots usar SCP (o un altre mètode) per copiar i veure aquesta imatge.")
                    print(f"Exemple per copiar la imatge al teu ordinador (executa en el TEU ORDINADOR):")
                    print(f"  scp pi@{os.uname().nodename}:{full_image_path} ./")
                    
                    user_input = input("\nHas verificat la imatge i és correcta? (s/n): ").lower().strip()
                    if user_input == 's':
                        print("Verificació de la imatge confirmada. Continuant el test.")
                        if cam._is_real_camera_simulated:
                            print("Recorda que aquesta imatge és simulada, ja que la càmera real no està disponible.")
                    else:
                        print("Verificació de la imatge NO confirmada. El test continuarà però amb avís.")
                        print("Això pot indicar un problema amb la teva càmera real o la configuració de PiCamera2.")
                        
                except Exception as e:
                    print(f"ERROR: No s'ha pogut desar la imatge per a verificació: {e}")
                    print("El test continuarà, però la verificació manual no ha estat possible.")
            else:
                print("ERROR: No s'ha pogut capturar la imatge. No hi ha res per verificar.")

            time.sleep(1) # Petita pausa

            # --- 2. Test de càmera no activa (sense interacció) ---
            print("\n--- 2. Test de captura amb càmera no activa ---")
            # Instanciem sense entrar al context per provar el missatge d'error
            cam_inactive = Camera(nom_camera="Càmera Inactiva")
            print(f"Estat de la càmera inactiva: {cam_inactive.get_camera_status()}")
            cam_inactive.capture_image_data() # Hauria de mostrar un missatge d'error i retornar None

    except Exception as e:
        print(f"\nS'ha produït un ERROR CRÍTIC durant el test de la càmera: {e}")
    finally:
        os.chdir(original_cwd) # Tornem al directori original
        print(f"\n--- Test de la Càmera Finalitzat. Tornat al directori original: {os.getcwd()} ---")
        # --- Neteja FINAL: Esborrar només el que aquest test ha creat ---
        clean_up_test_artifacts(test_env_path)
        print("Neteja dels artefactes del test completada.")


def clean_up_test_artifacts(test_base_path: str):
    """Neteja només els directoris i fitxers creats per aquest test."""
    print(f"\nIniciant neteja dels artefactes del test a: {test_base_path}...")
    if os.path.exists(test_base_path):
        try:
            shutil.rmtree(test_base_path)
            # print(f"Directori de prova '{test_base_path}' i contingut eliminat.")
        except OSError as e:
            print(f"ERROR en netejar el directori '{test_base_path}': {e}")
    else:
        print(f"Directori '{test_base_path}' ja no existeix, no cal netejar.")


# Quan s'executa el script directament, cridem la funció de test
if __name__ == "__main__":
    run_interactive_camera_test()
