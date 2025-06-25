#!/usr.bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import sys
import json
import threading

# Importa el GestorInstancies
from drivers.GestorInstancies import GestorInstancies
# Assegura't que la funció init_robot_components estigui en un fitxer accessible,
# per exemple, si està en el mateix fitxer main, no necessites la importació.
# Si està en un altre fitxer (ex: robot_setup.py), seria:
from drivers.initRobotComponents import init_robot_components # Assumeix que init_robot_components està a scripts/robot_setup.py


# --- Funció per trobar l'arrel del projecte (pot quedar aquí o en un mòdul d'utilitats) ---
def find_project_root(current_path):
    """
    Busca el directori arrel del projecte pujant per l'estructura de directoris
    fins que troba el fitxer '.project_root'.
    """
    while True:
        if os.path.exists(os.path.join(current_path, '.project_root')):
            return current_path
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path: # Arribat a la rel de l'arbre de directoris
            raise FileNotFoundError("No s'ha pogut trobar el fitxer '.project_root' en cap directori ascendent.")
        current_path = parent_path

# --- LÒGICA PRINCIPAL ---
if __name__ == "__main__":
    print("=====================================================")
    print("      Inici De La Preparacio dels Components")
    print("=====================================================\n")

    print("\n--- Localització de l'arrel del projecte i la configuració JSON ---")
    try:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = find_project_root(current_script_dir)
        print(f"Arrel del projecte trobada a: {project_root}")

        CONFIG_FILE_PATH = os.path.join(project_root, 'config', 'robot_config.json')

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR inesperat al localitzar l'arrel del projecte o la configuració: {e}")
        sys.exit(1)

    print("\n--- Càrrega de la configuració des del fitxer JSON ---")
    config_data = {}
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        print(f"Configuració carregada amb èxit des de: {CONFIG_FILE_PATH}\n")
    except FileNotFoundError:
        print(f"ERROR: El fitxer de configuració '{CONFIG_FILE_PATH}' no s'ha trobat.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"ERROR: El fitxer '{CONFIG_FILE_PATH}' no és un JSON vàlid. Revisa la seva sintaxi.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR inesperat al carregar la configuració: {e}")
        sys.exit(1)

    # Ús del GestorInstancies com a gestor de context principal
    with GestorInstancies() as gestor_instancies:
        try:
            # Crida a la funció centralitzada d'inicialització
            # Aquesta funció retorna un diccionari amb totes les instàncies inicialitzades
            instantiated_components = init_robot_components(gestor_instancies, config_data)

            # --- Assignació de les instàncies a variables directes per facilitar l'accés ---
            # Utilitzem .get() amb un valor per defecte None per si alguna instància no s'ha creat
            # (encara que en un sistema ben configurat, totes haurien d'estar presents)
            
            # Controladors de percepció i interacció
            camera = instantiated_components.get(config_data.get("camera", {}).get("nom")) # Usa el nom del JSON
            microphone = instantiated_components.get(config_data.get("microphone", {}).get("nom")) # Usa el nom del JSON
            altaveu = instantiated_components.get(config_data.get("altaveu", {}).get("nom")) # Usa el nom del JSON
            
            # Controladors de moviment
            motor_base = instantiated_components.get(config_data.get("motors_pas_a_pas", [{}])[0].get("nom")) # Assumint el primer motor_pas_a_pas és el de la base
            motor_articulacio_secundaria = instantiated_components.get(config_data.get("motors_pas_a_pas", [{}, {}])[1].get("nom")) # Assumint el segon motor_pas_a_pas és l'articulació secundaria
            motor_eix_z = instantiated_components.get(config_data.get("motors_pas_a_pas", [{}, {}, {}])[2].get("nom")) # Assumint el tercer motor_pas_a_pas és l'eix Z
            
            servomotor_canell = instantiated_components.get(config_data.get("servomotor", {}).get("nom")) # Usa el nom del JSON
            electroiman = instantiated_components.get(config_data.get("electroiman", {}).get("nom")) # Usa el nom del JSON
            
            # Gestors i controladors superiors
            file_manager = instantiated_components.get(config_data.get("file_manager", {}).get("nom")) # Usa el nom del JSON
            scara_controller = instantiated_components.get(config_data.get("scara_controller", {}).get("nom")) # Usa el nom del JSON

            print("\n--- Inciant proves amb els components inicialitzats ---")
            
            # --- Exemple: Accés a la càmera ---
            if camera:
                print(f"Càmera disponible: {camera.nom_camera}")
                # Aquí podries cridar mètodes de la càmera, per exemple:
                # time.sleep(1)
                # print("Previsualitzant càmera per 5 segons...")
                # camera.start_preview()
                # time.sleep(5)
                # camera.stop_preview()
                # print("Previsualització finalitzada.")
            else:
                print("La càmera no s'ha inicialitzat correctament o no està disponible.")

            # --- Exemple: Accés al micròfon ---
            if microphone:
                print(f"Micròfon disponible: {microphone.nom_microfon}")
                # Aquí podries cridar mètodes del micròfon
            else:
                print("El micròfon no s'ha inicialitzat correctament o no està disponible.")

            # --- Exemple: Accés a l'altaveu ---
            if altaveu:
                print(f"Altaveu disponible: {altaveu.nom_altaveu}")
                # Aquí podries cridar mètodes de l'altaveu
            else:
                print("L'altaveu no s'ha inicialitzat correctament o no està disponible.")

            # --- Exemple: Accés als motors pas a pas ---
            if motor_base:
                print(f"Motor de la base disponible: {motor_base.nom}")
            if motor_articulacio_secundaria:
                print(f"Motor de l'articulació secundària disponible: {motor_articulacio_secundaria.nom}")
            if motor_eix_z:
                print(f"Motor de l'eix Z disponible: {motor_eix_z.nom}")

            # --- Exemple: Accés al servomotor ---
            if servomotor_canell:
                print(f"Servomotor del canell disponible: {servomotor_canell.nom_servomotor}")
            
            # --- Exemple: Accés a l'electroimant ---
            if electroiman:
                print(f"Electroimant disponible: {electroiman.pin_control}")


            # --- Exemple: Accés al controlador SCARA ---
            if scara_controller:
                print(f"\nScaraController disponible.")
                print("--- Realitzant prova de calibratge del robot SCARA ---")
                scara_controller.calibrar_robot()
                time.sleep(2)

                print("\n--- Mou SCARA a una posició d'exemple (Base: 45, Art: 90, Z: 10, Canell: 90) ---")
                scara_controller.mou_a_posicio_eixos(45.0, 90.0, 10.0, 90.0, velocitat_index=0) # Velocitat ràpida
                time.sleep(3)

                print("\n--- Prova de l'electroimant (via ScaraController): Activa i desactiva ---")
                # ScaraController pot tenir mètodes per controlar l'electroimant
                # o accedir-hi directament si se li va passar la instància.
                if scara_controller.electroiman: # Si ScaraController guarda una referència a l'electroimant
                    print("Activació de l'electroimant via ScaraController...")
                    scara_controller.electroiman.activar()
                    time.sleep(2)
                    print("Desactivació de l'electroimant via ScaraController...")
                    scara_controller.electroiman.desactivar()
                    time.sleep(1)
                elif electroiman: # Si no, accedim directament a la variable global electroiman
                    print("Activació de l'electroimant directament des del main...")
                    electroiman.activar()
                    time.sleep(2)
                    print("Desactivació de l'electroimant directament des del main...")
                    electroiman.desactivar()
                    time.sleep(1)
                else:
                    print("Electroimant no disponible per a la prova.")
            else:
                print("ScaraController no s'ha inicialitzat correctament o no està disponible.")


            # --- Exemple: Accés a FileManager i prova de funcionalitat ---
            if file_manager:
                print(f"\nFileManager disponible. Directori base: {file_manager.base_directory}")
                
                # FileManager té accés a les instàncies que li van ser registrades (camera, microphone, altaveu)
                # La prova ara utilitza els objectes que FileManager té internament.
                if file_manager.camera:
                    print("FileManager té accés a la càmera. Realitzant prova de captura de foto...")
                    filepath = file_manager.take_photo(filename_prefix="prova_scara_")
                    if filepath:
                        print(f"Foto capturada a: {filepath}")
                    else:
                        print("No s'ha pogut capturar la foto amb FileManager (potser la càmera interna no es va inicialitzar o el mètode va fallar).")
                else:
                    print("FileManager no té accés a la càmera. No es pot capturar foto.")

                if file_manager.microphone:
                    print("FileManager té accés al micròfon.")
                    # file_manager.start_audio_recording(...)
                if file_manager.altaveu:
                    print("FileManager té accés a l'altaveu.")
                    # file_manager.play_audio(...)
            else:
                print("FileManager no s'ha inicialitzat correctament o no està disponible.")


            print("\n=====================================================")
            print("      Final De La Preparacio i Lògica Principal Completada")
            print("=====================================================\n")

        except Exception as e:
            print(f"\nS'ha produït un error inesperat durant l'execució: {e}")
            # L'excepció es propagarà a GestorInstancies.__exit__ per a la neteja

    print("Programa finalitzat.")