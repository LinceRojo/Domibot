#!/usr.bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import sys

# --- Importació de les classes de motors ---
# Assegura't que els fitxers MotorPasAPas.py, Servomotor.py i Electroiman.py
# es troben al mateix directori que aquest script de prova, o ajusta les rutes d'importació.
try:
    from MotorPasAPas import MotorPasAPas
    from Servomotor import Servomotor
    from Electroiman import Electroiman # Nova importació
except ImportError as e:
    print(f"ERROR: No s'ha pogut importar una de les classes de motor: {e}")
    print("Assegura't que els fitxers de les classes estan al mateix directori.")
    sys.exit(1)

# --- CONFIGURACIÓ DELS PINS GPIO ---
# *** IMPORTANT: Defineix els pins GPIO BCM per als teus motors aquí! ***
# Cada pin o llista de pins ha de ser única i no solapar-se.

PINS_MOTOR_PAS_A_PAS_1 = [4, 17, 27, 22] # Pins per al Motor Pas a Pas 1
PINS_MOTOR_PAS_A_PAS_2 = [24, 25, 8, 7]  # Pins per al Motor Pas a Pas 2
PINS_MOTOR_PAS_A_PAS_3 = [10, 9, 11, 5]   # Pins per al Motor Pas a Pas 3

PIN_SERVO = 12 # Pin per al Servomotor (per exemple, GPIO12)
PIN_ELECTROIMAN = 26 # Pin per a l'Electroimant (per exemple, GPIO26)

# --- VELOCITAT FIXA PER AL MOVIMENT DELS MOTORS PAS A PAS ---
VELOCITAT_FIXA_GRAUS_PER_SEGON = 90.0

# --- LÒGICA PRINCIPAL ---
if __name__ == "__main__":
    print("=====================================================")
    print("     Prova del ScaraController en Raspberry Pi")
    print("=====================================================\n")
    print("Aquest script inicialitzarà i configurarà 3 motors pas a pas, 1 servomotor i 1 electroimant.")
    print(f"La velocitat de moviment predeterminada per als motors pas a pas serà de: {VELOCITAT_FIXA_GRAUS_PER_SEGON:.1f}°/s.")
    print("Assegura't que tots els components estan correctament connectats als pins especificats.")
    print("Si un component no funciona, verifica el seu cablejat i l'assignació dels pins.\n")

    motors_pas_a_pas = []
    servomotor_instance = None
    electroiman_instance = None 

    try:
        # Configura el mode de numeració dels pins globalment (MOLT IMPORTANT: UNA VEGADA AL PRINCIPI)
        # Això assegura que totes les classes interpreten els números de pin de la mateixa manera.
        GPIO.setmode(GPIO.BCM)
        print("Mode GPIO establert a BCM.")

        # --- Configuració dels Motors Pas a Pas ---
        print("\n--- Creant i configurant les instàncies dels Motors Pas a Pas ---")
        motor1 = MotorPasAPas(
                              nom="Motor_Principal",
                              pins_in=PINS_MOTOR_PAS_A_PAS_1,
                              passos_per_volta_motor=32,
                              reduccio_engranatge=64.0,
                              mode_passos='half'
                             )
        motor1.setup_gpio()
        motor1.calibrar()
        motors_pas_a_pas.append(motor1)

        motor2 = MotorPasAPas(
                              nom="Motor_Auxiliar_1",
                              pins_in=PINS_MOTOR_PAS_A_PAS_2,
                              passos_per_volta_motor=32,
                              reduccio_engranatge=64.0,
                              mode_passos='half'
                             )
        motor2.setup_gpio()
        motor2.calibrar() 
        motors_pas_a_pas.append(motor2)

        motor3 = MotorPasAPas(
                              nom="Motor_Auxiliar_2",
                              pins_in=PINS_MOTOR_PAS_A_PAS_3,
                              passos_per_volta_motor=32,
                              reduccio_engranatge=64.0,
                              mode_passos='half'
                             )
        motor3.setup_gpio()
        motor3.calibrar() 
        motors_pas_a_pas.append(motor3)

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
            duty_cycle_min=2.190,
            duty_cycle_max=12.290,
            angle_min_operational=0,
            angle_max_operational=180
        )
        servomotor_instance.__enter__() # Crida manual a __enter__ per configurar el servo

        # --- Configuració de l'Electroimant ---
        print(f"\n--- Creant i configurant la instància de l'Electroimant al Pin {PIN_ELECTROIMAN} ---")
        electroiman_instance = Electroiman(pin_control=PIN_ELECTROIMAN)
        electroiman_instance.setup() # Crida manual a setup() per configurar l'electroimant

        # --- Fi Configuracio ns de les clases  ----
        print("\n---              ---                  ---                   ---               ---")
        print("\n--- Tots els components (motors i electroimant) creats i configurats amb èxit ---")
        print("\n---              ---                  ---                   ---               ---")



        #TODO:posar les proves a fer aqui


        # --- Fi De les Pproves  ----
        print("\n---              ---                  ---                   ---               ---")
        print("\n---     Totes les proves a realitzar amb ScaraController s'han realitzat.     ---")
        print("\n---              ---                  ---                   ---               ---")

    except Exception as e:
        print(f"\nS'ha produït un error inesperat: {e}")
    finally:
        print("\n--- Iniciant neteja final de GPIO per a tots els components ---")
        # Neteja dels motors pas a pas
        for motor in motors_pas_a_pas:
            if hasattr(motor, '_is_setup') and motor._is_setup:
                motor.cleanup_gpio()
            else:
                print(f"Saltant neteja de '{motor.nom}': no es va inicialitzar.")
        
        # Neteja del servomotor
        if servomotor_instance:
            if hasattr(servomotor_instance, '_is_setup') and servomotor_instance._is_setup:
                servomotor_instance.__exit__(None, None, None)
            else:
                print(f"Saltant neteja de '{servomotor_instance.nom}': no es va inicialitzar.")

        # Neteja de l'electroimant
        if electroiman_instance:
            if electroiman_instance._construit: # Utilitzem _construit per saber si es va configurar
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
