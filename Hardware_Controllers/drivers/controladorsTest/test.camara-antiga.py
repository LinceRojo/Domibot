# Exemple d'ús al teu script principal

# Assegura't que les classes estiguin en fitxers Camera.py i CameraFileManager.py
# O importa-les segons la teva estructura de projecte.
# Per exemple:
# from your_module.Camera import Camera
# from your_module.CameraFileManager import CameraFileManager

import time
import RPi.GPIO as GPIO # Sovint s'utilitza amb càmeres i motors, així que la incloc
from scripts.CameraFileManager import CameraFileManager
from scripts.Camera import Camera

try:
    # ----------------------------------------------------
    # Exemple 1: Ús bàsic de la càmera amb el gestor de context (RECOMANAT)
    # ----------------------------------------------------
    print("\n--- Exemple 1: Ús bàsic amb 'with' ---")
    with Camera(nom_camera="Càmera Principal", default_prefix="foto_lab") as cam:
        # La càmera ja està configurada i iniciada quan entrem aquí
        print(f"La càmera '{cam.nom}' està { 'activa' if cam.get_camera_status() else 'inactiva' }.")

        # Pots fer una captura
        filepath = cam.save_image(extension="png") # Guarda com a PNG per millor qualitat
        if filepath:
            print(f"Imatge guardada amb èxit a: {filepath}")
        else:
            print("No s'ha pogut guardar la imatge.")
        
        time.sleep(1) # Espera un moment

        # Prova una segona captura
        filepath2 = cam.save_image(extension="jpg")
        if filepath2:
            print(f"Segona imatge guardada amb èxit a: {filepath2}")

        print("\nHistorial de captures:")
        for path in cam.get_capture_history():
            print(f"- {path}")
        
        print(f"Última captura: {cam.get_last_capture_path()}")

        # Simular un error per veure si __exit__ funciona
        # raise ValueError("Això és un error simulat!")

    print("Fora del bloc 'with'. La càmera hauria d'estar aturada i els recursos alliberats.")
    print(f"Estat final de la càmera: { 'activa' if cam.get_camera_status() else 'inactiva' }.")

    # ----------------------------------------------------
    # Exemple 2: Canviar el directori de captures del File Manager
    # ----------------------------------------------------
    print("\n--- Exemple 2: Canviar el directori de captures ---")
    with Camera(nom_camera="Càmera Secundària", capture_dir="altres_fotos", default_prefix="altre_prefix") as cam2:
        print(f"El directori base actual per a cam2 és: {cam2.get_file_manager().get_base_directory()}")
        cam2.save_image() # Guarda una imatge al directori "altres_fotos"

        # Ara, canviem el directori base
        cam2.get_file_manager().set_base_directory("noves_captures")
        print(f"El directori base actualitzat per a cam2 és: {cam2.get_file_manager().get_base_directory()}")
        cam2.save_image() # Guarda una imatge al directori "noves_captures"

    # ----------------------------------------------------
    # Exemple 3: Calibratge i neteja global (si cal)
    # ----------------------------------------------------
    # Si tens altres components GPIO, pots fer una neteja final.
    # En un programa real, potser només crides GPIO.cleanup() una vegada al final.
    # GPIO.cleanup() # Neteja global de tots els pins GPIO si s'han usat
    # print("\nNeteja global de GPIOs completada (si s'han usat).")

except Exception as e:
    print(f"\nS'ha produït un error inesperat en el script principal: {e}")
finally:
    # Una neteja final global de GPIO és una bona pràctica si no saps exactament
    # quins pins estan configurats o si tens múltiples dispositius GPIO.
    # Si les teves classes de motors i càmeres ja fan cleanup al seu __exit__ o __del__,
    # aquesta línia és principalment una salvaguarda.
    # GPIO.cleanup() 
    pass # La neteja es gestiona pels context managers.
