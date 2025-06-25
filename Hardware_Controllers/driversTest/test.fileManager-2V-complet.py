#!/usr.bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import RPi.GPIO as GPIO
import sys

# --- Importació de les classes de motors ---
# Assegura't que els fitxers de les classes que necessites
# es troben al mateix directori que aquest script de prova, o ajusta les rutes d'importació.
try:
    from scripts.controladors.Camera import Camera
    from scripts.controladors.Microphone import Microphone
    from scripts.controladors.Altaveu import Altaveu # Importem la classe Altaveu
    from scripts.FileManager import FileManager
except ImportError as e:
    print(f"ERROR: No s'ha pogut importar una de les classes de component: {e}")
    print("Assegura't que els fitxers de les classes estan al mateix directori o en les rutes d'importació correctes.")
    sys.exit(1)

# --- CONFIGURACIÓ DELS PINS GPIO ---
# *** IMPORTANT: Defineix els pins GPIO BCM per als teus components aquí! ***
# Cada pin o llista de pins ha de ser única i no solapar-se.

# Ja no es necessiten pins per a motors, servomotors o electroimants

# --- LÒGICA PRINCIPAL ---
if __name__ == "__main__":
    print("=====================================================")
    print("      Prova dels Components de Control en Raspberry Pi")
    print("=====================================================\n")
    print("Aquest script inicialitzarà i configurarà els components de càmera, micròfon i altaveu.")
    print("Assegura't que tots els components estan correctament connectats als pins especificats.")
    print("Si un component no funciona, verifica el seu cablejat i l'assignació dels pins.\n")

    ins_camara = None
    ins_microphone = None
    ins_altaveu = None # Declarar la variable per a la instància de l'altaveu

    try:
        # Configura el mode de numeració dels pins globalment (MOLT IMPORTANT: UNA VEGADA AL PRINCIPI)
        # Això assegura que totes les classes interpreten els números de pin de la mateixa manera.
        GPIO.setmode(GPIO.BCM)
        print("Mode GPIO establert a BCM.")

        # --- Configuració de la Camara ---
        print("\n--- Creant i configurant la instància de la Camara ---")
        ins_camara = Camera(
            nom_camera="CàmeraAuxiliar",
            resolucio=(3280,2464),
            default_extension="jpg"
        )
        ins_camara.__enter__() # Crida manual a __enter__

        print("\n--- Instància de la camara creada i configurada ---")


        # --- Configuració del Microphone ---
        print(f"\n--- Creant i configurant la instància del Microphone ---")
        ins_microphone = Microphone(
            nom_microfon="MicSPH0645_Sinc",
            samplerate=48000,
            channels=1
        )
        ins_microphone.__enter__() # Crida manual a __enter__ per configurar el Microphone

        # --- Configuració de l'Altaveu ---
        print(f"\n--- Creant i configurant la instància de l'Altaveu ---")
        ins_altaveu = Altaveu(
            nom_altaveu="Altaveu Principal",
            device_label_alsa=None # O el teu dispositiu ALSA específic
        )
        ins_altaveu.__enter__() # Crida manual a __enter__ per configurar l'Altaveu

        print("\n---             ---                  ---                     ---               ---")
        print("\n--- Tots els components (càmera, micròfon i altaveu) creats i configurats amb èxit ---")
        print("\n---             ---                  ---                     ---               ---")


        #TODO:posar les proves a fer aqui
        print("\n--- Iniciant proves amb FileManager ---")
        # Crea una instància de FileManager
        file_manager_instance = FileManager(
            base_directory="captures_proves_fm", # Aquesta serà la subcarpeta dins de 'dades'
            default_prefix="scara_test",
            scripts_folder_name="scripts", # Ajusta si el teu directori de scripts té un nom diferent
            data_folder_name="dades" # Ajusta si el teu directori de dades té un nom diferent
        )
        print("Instància de FileManager creada amb èxit.")


       # --- Registre dels components amb FileManager ---
        print("\n--- Registrant instàncies de maquinari amb FileManager ---")

        is_camara = False
        is_microphone = False
        is_altaveu = False
        if ins_camara:
            file_manager_instance.register_camera(ins_camara)
            is_camara = True
        if ins_microphone:
            file_manager_instance.register_microphone(ins_microphone)
            is_microphone = True
        if ins_altaveu:
            file_manager_instance.register_speaker(ins_altaveu)
            is_altaveu = True
        print("Registre de components amb FileManager completat.")

        # --- Inici proves amb FileManager --- 
        print("--- Inici proves amb FileManager ---")

        # --- Prova de captura de foto ---
        if is_camara:
            print("\n--- Provant a prendre una foto amb FileManager ---")
            photo_filepath = file_manager_instance.take_photo()
            if photo_filepath:
                print(f"Foto guardada amb èxit a: {photo_filepath}")
            else:
                print("ERROR: No s'ha pogut prendre la foto.")
            time.sleep(1) # Pausa per visualitzar la sortida
        else:
            print("\n--- ERROR instancia camara no iniciada ---")
        # --- Prova de gravació d'àudio ---

        if is_microphone:
            print("\n--- Provant a gravar àudio amb FileManager (5 segons) ---")
            audio_filepath = file_manager_instance.record_audio(duration=5)
            if audio_filepath:
                print(f"Àudio gravat amb èxit a: {audio_filepath}")
            else:
                print("ERROR: No s'ha pogut gravar l'àudio.")
            time.sleep(1) # Pausa
        else:
            print("\n--- ERROR instancia microphone no iniciada ---")
        # --- Prova de llistat d'historial ---
        print("\n--- Llistant historial de captures ---")
        history = file_manager_instance.get_capture_history()
        if history:
            print(f"Historial actual ({len(history)} entrades):")
            for i, entry in enumerate(history):
                print(f"  [{i}] Tipus: {entry.get('content_type')}, Fitxer: {entry.get('filename')}, Hora: {entry.get('timestamp')}")
        else:
            print("L'historial de captures està buit.")
        time.sleep(1) # Pausa

        # --- Prova de reproducció d'àudio des de l'historial ---
        if is_altaveu:
            if audio_filepath:
                print("\n--- Provant a reproduir l'àudio recentment gravat ---")
                # Podem usar el nom del fitxer o l'índex (si sabem que és l'últim)
                success_play = file_manager_instance.play_audio_from_history(os.path.basename(audio_filepath))
                if success_play:
                    print("Reproducció d'àudio iniciada amb èxit.")
                else:
                    print("ERROR: No s'ha pogut reproduir l'àudio.")
                time.sleep(6) # Donem temps a que l'àudio es reprodueixi (durada + 1 segon)
            else:
                print("\n--- No hi ha àudio per reproduir (gravació fallida) ---")
        else:
            print("\n--- ERROR instancia microphone no iniciada ---")

        # --- Fi de les proves amb FileManager ---

        print("\n---             ---                  ---                     ---               ---")
        print("\n---     Totes les proves a realitzar amb els components s'han realitzat.      ---")
        print("\n---             ---                  ---                     ---               ---")

    except Exception as e:
        print(f"\nS'ha produït un error inesperat: {e}")
    finally:
        print("\n--- Iniciant neteja final de GPIO per a tots els components ---")
        
        # Neteja de la Càmera
        if ins_camara:
            print("Netejant càmera...")
            ins_camara.__exit__(None, None, None) # Crida manual a __exit__

        # Neteja del Microphone
        if ins_microphone:
            print("Netejant microphone...")
            ins_microphone.__exit__(None, None, None) # Crida manual a __exit__

        # Neteja de l'Altaveu
        if ins_altaveu:
            print("Netejant altaveu...")
            ins_altaveu.__exit__(None, None, None) # Crida manual a __exit__

        # Neteja global final de GPIO per assegurar que tots els pins s'alliberen
        try:
            GPIO.cleanup()
            print("Neteja de GPIO global completada.")
        except RuntimeWarning as w:
            print(f"Avís durant la neteja global de GPIO: {w}")
        except Exception as e:
            print(f"Error durant la neteja global de GPIO: {e}")

        print("Programa finalitzat.")
