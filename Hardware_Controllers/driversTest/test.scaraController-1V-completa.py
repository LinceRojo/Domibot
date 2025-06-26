#!/usr.bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import sys

# --- Importació de les classes de motors ---
# Assegura't que els fitxers MotorPasAPas.py, Servomotor.py i Electroiman.py
# es troben al mateix directori que aquest script de prova, o ajusta les rutes d'importació.
try:
    from scripts.controladors.MotorPasAPasNoNormalitzat import MotorPasAPas
    from scripts.controladors.Servomotor import Servomotor
    from scripts.controladors.Electroiman import Electroiman # Nova importació
    from scripts.ScaraController import ScaraController # Importació de la classe a provar
except ImportError as e:
    print(f"ERROR: No s'ha pogut importar una de les classes de motor: {e}")
    print("Assegura't que els fitxers de les classes estan al mateix directori.")
    sys.exit(1)

# --- CONFIGURACIÓ DELS PINS GPIO ---
# *** IMPORTANT: Defineix els pins GPIO BCM per als teus motors aquí! ***
# Cada pin o llista de pins ha de ser única i no solapar-se.

PINS_MOTOR_PAS_A_PAS_1 = [4, 17, 27, 22] # Pins per al Motor Pas a Pas 1 (Base)
PINS_MOTOR_PAS_A_PAS_2 = [24, 25, 8, 7]  # Pins per al Motor Pas a Pas 2 (Articulació Secundària)
PINS_MOTOR_PAS_A_PAS_3 = [10, 9, 11, 5]  # Pins per al Motor Pas a Pas 3 (Eix Z)

PIN_SERVO = 12 # Pin per al Servomotor (Canell)
PIN_ELECTROIMAN = 26 # Pin per a l'Electroimant

# --- VELOCITAT FIXA PER AL MOVIMENT DELS MOTORS PAS A PAS ---
VELOCITAT_FIXA_GRAUS_PER_SEGON = 90.0

# --- CONFIGURACIÓ DE L'ESCENARI PER AL SCARACONTROLLER ---
# Aquesta configuració s'ajusta als paràmetres que espera la classe ScaraController
SCARA_CONFIG = {
    "base": {
        "limits": (-90.0, 90.0), # Graus de l'articulació
        "speeds": [120.0, 60.0, 30.0], # Graus/segon (de la més ràpida a la més lenta)
        "offset": 0.0, # Posició 0 lògica
        "reduction_ratio": 1.0 # Relació entre graus de l'articulació / graus del motor
    },
    "articulacio_secundaria": {
        "limits": (0.0, 180.0),
        "speeds": [120.0, 60.0, 30.0],
        "offset": 0.0,
        "reduction_ratio": 1.0
    },
    "eix_z": {
        "limits": (-50.0, 50.0), # Altura Z (pots ajustar-ho segons el teu robot)
        "speeds": [90.0, 45.0, 20.0],
        "offset": 0.0,
        "reduction_ratio": 1.0
    },
    "canell": {
        "limits": (0.0, 180.0),
        "speeds": [0.05, 0.1, 0.2], # Delay en segons (el més ràpid és el delay més petit)
        "offset": 90.0, # Posició central del canell
        "reduction_ratio": 1.0
    }
}

# --- LÒGICA PRINCIPAL ---
if __name__ == "__main__":
    print("=====================================================")
    print("       Prova del ScaraController en Raspberry Pi")
    print("=====================================================\n")
    print("Aquest script inicialitzarà i configurarà 3 motors pas a pas, 1 servomotor i 1 electroimant.")
    print(f"La velocitat de moviment predeterminada per als motors pas a pas serà de: {VELOCITAT_FIXA_GRAUS_PER_SEGON:.1f}°/s.")
    print("Assegura't que tots els components estan correctament connectats als pins especificats.")
    print("Si un component no funciona, verifica el seu cablejat i l'assignació dels pins.\n")

    motors_pas_a_pas = []
    servomotor_instance = None
    electroiman_instance = None
    scara_controller = None

    try:
        # Configura el mode de numeració dels pins globalment (MOLT IMPORTANT: UNA VEGADA AL PRINCIPI)
        # Això assegura que totes les classes interpreten els números de pin de la mateixa manera.
        GPIO.setmode(GPIO.BCM)
        print("Mode GPIO establert a BCM.")

        # --- Configuració dels Motors Pas a Pas ---
        print("\n--- Creant i configurant les instàncies dels Motors Pas a Pas ---")
        motor_base = MotorPasAPas(
                                 nom="Motor_Base",
                                 pins_in=PINS_MOTOR_PAS_A_PAS_1,
                                 passos_per_volta_motor=32,
                                 reduccio_engranatge=64.0,
                                 mode_passos='half'
                                )
        motor_base.setup_gpio()
        motor_base.calibrar()
        motors_pas_a_pas.append(motor_base)

        motor_articulacio_secundaria = MotorPasAPas(
                                                 nom="Motor_Articulacio_Secundaria",
                                                 pins_in=PINS_MOTOR_PAS_A_PAS_2,
                                                 passos_per_volta_motor=32,
                                                 reduccio_engranatge=64.0,
                                                 mode_passos='half'
                                                )
        motor_articulacio_secundaria.setup_gpio()
        motor_articulacio_secundaria.calibrar()
        motors_pas_a_pas.append(motor_articulacio_secundaria)

        motor_eix_z = MotorPasAPas(
                                   nom="Motor_Eix_Z",
                                   pins_in=PINS_MOTOR_PAS_A_PAS_3,
                                   passos_per_volta_motor=32,
                                   reduccio_engranatge=64.0,
                                   mode_passos='half'
                                  )
        motor_eix_z.setup_gpio()
        motor_eix_z.calibrar()
        motors_pas_a_pas.append(motor_eix_z)

        print("\n--- Totes les instàncies de motors pas a pas creades i configurades amb èxit ---")
        for i, motor in enumerate(motors_pas_a_pas):
            print(f"Motor Pas a Pas {i+1}: '{motor.nom}' (Pins: {motor.pins_in})")
            print(f"  Posició actual: {motor.obtenir_posicio_graus():.2f}°")

        # --- Configuració del Servomotor ---
        print(f"\n--- Creant i configurant la instància del Servomotor al Pin {PIN_SERVO} ---")
        servomotor_instance = Servomotor(
            nom_servomotor="Braç_Servo",
            pin_gpio=PIN_SERVO,
            pwm_frequency=50,
            duty_cycle_min=2.190, # Ajusta segons el teu servomotor
            duty_cycle_max=12.290, # Ajusta segons el teu servomotor
            angle_min_operational=0,
            angle_max_operational=180
        )
        servomotor_instance.__enter__() # Crida manual a __enter__ per configurar el servo

        # --- Configuració de l'Electroimant ---
        print(f"\n--- Creant i configurant la instància de l'Electroimant al Pin {PIN_ELECTROIMAN} ---")
        electroiman_instance = Electroiman(pin_control=PIN_ELECTROIMAN)
        electroiman_instance.setup() # Crida manual a setup() per configurar l'electroimant

        # --- Fi Configuració de les classes ----
        print("\n------------------------------------------------------------------")
        print("\n--- Tots els components (motors i electroimant) creats i configurats amb èxit ---")
        print("\n------------------------------------------------------------------")

        # --- Creació de la instància de ScaraController ---
        print("\n--- Creant la instància de ScaraController per a les proves ---")
        scara_controller = ScaraController(
            motor_base=motor_base,
            motor_articulacio_secundaria=motor_articulacio_secundaria,
            motor_eix_z=motor_eix_z,
            servomotor_canell=servomotor_instance,
            electroiman=electroiman_instance,
            config=SCARA_CONFIG
        )
        print("Instància de ScaraController creada amb èxit.")
        time.sleep(1) # Petit retard per a la lectura

        # --- Inici de les proves amb ScaraController ---
        print("\n--- INICIANT LES PROVES AMB SCARACONTROLLER ---")
        print("\n------------------------------------------------------------------")

        # Prova 1: Calibratge del robot
        print("\n--- Prova 1: Calibratge del robot ---")
        scara_controller.calibrar_robot()
        time.sleep(2)

        # Prova 2: Moure un sol eix (Base)
        print("\n--- Prova 2: Moure sol eix (Base a 45 graus) ---")
        # Utilitzem els ID d'eix definits a la classe ScaraController
        scara_controller.moure_sol_eix(ScaraController.EIX_BASE, 45.0, velocitat_index=0) # Velocitat ràpida
        time.sleep(2)

        # Prova 3: Moure un sol eix (Articulació Secundària)
        print("\n--- Prova 3: Moure sol eix (Articulació Secundària a 90 graus) ---")
        scara_controller.moure_sol_eix(ScaraController.EIX_ARTICULACIO_SECUNDARIA, 90.0, velocitat_index=1) # Velocitat normal
        time.sleep(2)

        # Prova 4: Moure un sol eix (Eix Z)
        print("\n--- Prova 4: Moure sol eix (Eix Z a 20 graus) ---")
        scara_controller.moure_sol_eix(ScaraController.EIX_Z, 20.0, velocitat_index=-1) # Velocitat lenta
        time.sleep(2)

        # Prova 5: Moure un sol eix (Canell)
        print("\n--- Prova 5: Moure sol eix (Canell a 0 graus) ---")
        scara_controller.moure_sol_eix(ScaraController.EIX_CANELL, 0.0, velocitat_index=0) # Velocitat ràpida
        time.sleep(2)
        print("\n--- Prova 5b: Moure sol eix (Canell a 180 graus) ---")
        scara_controller.moure_sol_eix(ScaraController.EIX_CANELL, 180.0, velocitat_index=-1) # Velocitat lenta
        time.sleep(2)
        print("\n--- Prova 5c: Moure sol eix (Canell de tornada a 90 graus) ---")
        scara_controller.moure_sol_eix(ScaraController.EIX_CANELL, 90.0) # Velocitat per defecte
        time.sleep(2)


        # Prova 6: Moure tots els eixos concurrentment a una posició
        print("\n--- Prova 6: Moure tots els eixos a una nova posició (concurrent) ---")
        # Anem a una posició (Base= -30, Artic_Sec= 60, Z= -10, Canell= 30)
        target_pos_1 = (-30.0, 60.0, -10.0, 30.0)
        scara_controller.mou_a_posicio_eixos(target_pos_1[0], target_pos_1[1], target_pos_1[2], target_pos_1[3], velocitat_index=0) # Velocitat ràpida
        time.sleep(3) # Donar temps perquè el moviment concurrent es completi

        # Prova 7: Moure a una altra posició (concurrent)
        print("\n--- Prova 7: Moure tots els eixos a una altra posició (concurrent) ---")
        # Anem a una posició (Base= 60, Artic_Sec= 120, Z= 30, Canell= 150)
        target_pos_2 = (60.0, 120.0, 30.0, 150.0)
        scara_controller.mou_a_posicio_eixos(target_pos_2[0], target_pos_2[1], target_pos_2[2], target_pos_2[3], velocitat_index=-1) # Velocitat lenta
        time.sleep(3)


        # Prova 8: Gestionar objecte (agafar)
        print("\n--- Prova 8: Gestionar objecte (AGAFAR) ---")
        # Posició de l'objecte (assumint que és la mateixa que l'última posició assolida a la prova 7)
        posicio_objecte_per_agafar = target_pos_2
        altura_seguretat = SCARA_CONFIG["eix_z"]["limits"][1] - 10 # 10 graus per sota del límit superior de Z
        scara_controller.gestionar_objecte(posicio_objecte_per_agafar, altura_seguretat, agafar_objecte=True)
        time.sleep(2)


        # Prova 9: Moure a una nova posició amb l'objecte agafat
        print("\n--- Prova 9: Moure a una nova posició amb l'objecte agafat ---")
        # Anem a una posició (Base= 0, Artic_Sec= 45, Z= 10, Canell= 90) amb l'objecte
        target_pos_3 = (0.0, 45.0, 10.0, 90.0)
        scara_controller.mou_a_posicio_eixos(target_pos_3[0], target_pos_3[1], target_pos_3[2], target_pos_3[3], velocitat_index=-2) # Velocitat per defecte
        time.sleep(3)


        # Prova 10: Gestionar objecte (deixar anar)
        print("\n--- Prova 10: Gestionar objecte (DEIXAR ANAR) ---")
        # Posició on es deixa anar l'objecte (assumint l'última posició)
        posicio_objecte_per_deixar = target_pos_3
        scara_controller.gestionar_objecte(posicio_objecte_per_deixar, altura_seguretat, agafar_objecte=False)
        time.sleep(2)

        # Prova 11: Aturada d'emergència i posterior calibratge
        print("\n--- Prova 11: Aturada d'Emergència i Calibratge posterior ---")
        scara_controller.aturada_emergencia()
        time.sleep(2)
        scara_controller.calibrar_robot()
        time.sleep(2)

        # Prova 12: Moure a una posició fora de límits (esperant error)
        print("\n--- Prova 12: Intentar moure l'eix Base fora de límits (esperant advertència/error) ---")
        scara_controller.moure_sol_eix(ScaraController.EIX_BASE, 100.0) # Fora del límit de 90
        time.sleep(1)

        print("\n------------------------------------------------------------------")
        print("\n---         Totes les proves a realitzar amb ScaraController s'han realitzat.         ---")
        print("\n------------------------------------------------------------------")

    except Exception as e:
        print(f"\nS'ha produït un error inesperat: {e}")
    finally:
        print("\n--- Iniciant neteja final de GPIO per a tots els components ---")
        # Neteja dels motors pas a pas
        for motor in motors_pas_a_pas:
            # Comprovem si l'atribut _is_setup existeix abans d'intentar accedir-hi
            if hasattr(motor, '_is_setup') and motor._is_setup:
                motor.cleanup_gpio()
            else:
                print(f"Saltant neteja de '{motor.nom}': no es va inicialitzar.")

        # Neteja del servomotor
        if servomotor_instance:
            if hasattr(servomotor_instance, '_is_setup') and servomotor_instance._is_setup:
                servomotor_instance.__exit__(None, None, None)
            else:
                print(f"Saltant neteja de '{servomotor_instance.nom_servomotor}': no es va inicialitzar.")

        # Neteja de l'electroimant
        if electroiman_instance:
            # Comprovem si l'atribut _construit existeix
            if hasattr(electroiman_instance, '_construit') and electroiman_instance._construit: # Utilitzem _construit per saber si es va configurar
                electroiman_instance.cleanup()
            else:
                print(f"Saltant neteja de l'electroimant (pin {electroiman_instance.pin_control}): no es va configurar correctament.")

        # Neteja global final de GPIO per assegurar que tots els pins s'alliberen
        try:
            GPIO.cleanup()
            print("Neteja de GPIO global completada.")
        except RuntimeWarning as w:
            print(f"Avís durant la neteja global de GPIO: {w}")
        except Exception as e:
            print(f"Error durant la neteja global de GPIO: {e}")

        print("Programa finalitzat.")
