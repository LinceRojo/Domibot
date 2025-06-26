#!/usr.bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import sys

# --- CONFIGURACIÓ DE LA CLASSE MOTORPASAPAS ---
# IMPORTANT: Ajusta aquesta línia segons la ubicació real del teu fitxer MotorPasAPas.
# Si MotorPasAPasNoNormalitzat.py està directament al mateix directori:
# from MotorPasAPasNoNormalitzat import MotorPasAPas
#
# Si està en 'scripts/controladors/MotorPasAPasNoNormalitzat.py', podries necessitar:
# sys.path.append('/ruta/al/directori/pare/del/vostre/projecte')
# from scripts.controladors.MotorPasAPasNoNormalitzat import MotorPasAPas

try:
    from scripts.controladors.MotorPasAPasNoNormalitzat import MotorPasAPas
except ImportError:
    print("ERROR: No s'ha pogut importar la classe MotorPasAPasNoNormalitzat.")
    print("Assegura't que el fitxer 'MotorPasAPasNoNormalitzat.py' es troba al mateix directori")
    print("que aquest script, o que la ruta d'importació és correcta.")
    sys.exit(1)

# --- CONFIGURACIÓ DELS PINS GPIO ---
# *** IMPORTANT: Defineix els pins GPIO per al teu motor pas a pas aquí! ***
# Utilitza la numeració BCM. Aquests són pins d'exemple, AJUSTA'LS al teu cablejat.
PINS_MOTOR_PAS_A_PAS = [10, 9, 11, 5] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    #PINS_MOTOR_PAS_A_PAS = [4, 17, 27, 22] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    #PINS_MOTOR_PAS_A_PAS = [24, 25, 8, 7] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    #PINS_MOTOR_PAS_A_PAS = [10, 9, 11, 5] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
# --- VELOCITAT FIXA PER AL MOVIMENT ---
VELOCITAT_FIXA_GRAUS_PER_SEGON = 90.0 # Pots ajustar aquesta velocitat segons necessitis

def obtenir_graus_usuari(missatge):
    """
    Sol·licita a l'usuari que introdueixi un valor en graus
    i valida que sigui un número.
    """
    while True:
        try:
            graus_str = input(missatge).strip()
            if graus_str.lower() == 'q':
                return None
            graus = float(graus_str)
            return graus
        except ValueError:
            print("Entrada invàlida. Si us plau, introdueix un número per als graus, o 'q' per sortir.")

# --- LÒGICA PRINCIPAL ---
if __name__ == "__main__":
    print("=====================================================")
    print("  Control Manual Simple de Motor Pas a Pas (POSICIÓ ABSOLUTA)")
    print("=====================================================\n")
    print(f"Utilitzant pins GPIO BCM: {PINS_MOTOR_PAS_A_PAS}.")
    print(f"La velocitat de moviment serà fixa a: {VELOCITAT_FIXA_GRAUS_PER_SEGON:.1f}°/s.")
    print("Assegura't que el motor i el driver estan correctament connectats.\n")

    motor = None # Inicialitzem a None per al bloc finally

    try:
        # Utilitzem el gestor de context 'with' per assegurar una neteja adequada de GPIO
        with MotorPasAPas(
            nom="Motor_Simple",
            pins_in=PINS_MOTOR_PAS_A_PAS,
            passos_per_volta_motor=32,
            reduccio_engranatge=64.0,
            mode_passos='half'
        ) as motor:
            print(f"Motor '{motor.nom}' inicialitzat.")
            print(f"Total de passos per volta: {motor.passos_per_volta}")
            print(f"Angle mínim per pas: {motor.min_angle_per_step:.4f}°")

            # --- Calibratge Inicial (un cop a l'inici) ---
            print("\n--- INICI: CALIBRATGE AUTOMÀTIC ---")
            print("El motor es mourà ara per establir la seva posició de referència (0°).")
            print("Això simula que troba un final de carrera movent-se enrere.")
            input("Premeu Intro per iniciar el calibratge (el motor es mourà automàticament)...\n")
            
            motor.calibrar(
                grausAMoure=0, # Busca el 0° en la pocico actual
                direccio_calibratge=MotorPasAPas.DIRECCIO_ENRERE, # O ENDAVANT, segons el teu setup físic
                velocitat_graus_per_segon=VELOCITAT_FIXA_GRAUS_PER_SEGON # Utilitzem la velocitat fixa
            )
            print(f"Motor calibrat. Posició actual (absoluta): {motor.obtenir_posicio_graus():.2f}°")
            print(f"Posició normalitzada (0-360): {motor.obtenir_posicio_graus_normalitzada():.2f}°")

            print("\n--- CONTROL DE POSICIÓ EN BUCLE ---")
            print("Introdueix els graus objectiu per moure el motor (p. ex., 90, 180, 270, 360, -90).")
            print("Escriu 'q' i prem Intro per sortir del programa.")

            while True:
                graus_objectiu = obtenir_graus_usuari("\nIntrodueix els graus objectiu [q per sortir]: ")

                if graus_objectiu is None: # L'usuari ha escrit 'q'
                    break

                print(f"\nSol·licitud: Moure a {graus_objectiu}° a {VELOCITAT_FIXA_GRAUS_PER_SEGON:.1f}°/s...")
                
                # Mou el motor a la posició absoluta desitjada amb la velocitat fixa
                motor.moure_a_graus(graus_objectiu, velocitat_graus_per_segon=VELOCITAT_FIXA_GRAUS_PER_SEGON)
                
                print(f"Moviment completat. Posició actual (absoluta): {motor.obtenir_posicio_graus():.2f}°")
                print(f"Posició actual (normalitzada 0-360): {motor.obtenir_posicio_graus_normalitzada():.2f}°")
                
                # Una pausa breu per estabilitat abans de la següent petició
                time.sleep(0.5)

    except Exception as e:
        print(f"\nS'ha produït un error inesperat: {e}")
    finally:
        print("\nPrograma finalitzat.")
        print("Realitzant neteja final de GPIO...")
        try:
            # GPIO.cleanup() sense arguments neteja tots els pins que han estat configurats
            GPIO.cleanup() 
            print("Neteja de GPIO completada.")
        except RuntimeWarning:
            print("Avís: Intent de netejar pins que ja estan nets.")
        except Exception as e:
            print(f"Error durant la neteja de GPIO: {e}")
