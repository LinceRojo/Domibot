#!/usr.bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
# Importem la classe MotorPasAPas. Ajusta la ruta si és diferent.
# Si la classe MotorPasAPas està en el mateix directori que aquest script de proves,
# pots importar-la directament:
from scripts.controladors.MotorPasAPasNoNormalitzat import MotorPasAPas 
# Assumeix que la classe està en MotorPasAPas.py

# Funció per esperar la interacció de l'usuari
def esperar_per_continuar(missatge="Premeu Intro per continuar..."):
    """
    Pausa l'execució del programa fins que l'usuari premeu Intro.
    """
    input(missatge)

# ----------- Lògica de prova -----------
if __name__ == "__main__":
    # *** IMPORTANT: Defineix els pins GPIO per al teu motor pas a pas aquí! ***
    # Utilitza la numeració BCM. Aquests són pins d'exemple, AJUSTA'LS al teu cablejat.
    # Posa uns pins que estiguin lliures i que siguin OUT.
    # Exemples:
    # GPIO2, GPIO3, GPIO4, GPIO17 (pins físics 3, 5, 7, 11)
    #PINS_MOTOR_PAS_A_PAS = [4, 17, 27, 22] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    #PINS_MOTOR_PAS_A_PAS = [24, 25, 8, 7] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    PINS_MOTOR_PAS_A_PAS = [10, 9, 11, 5] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)

    print("Iniciant prova de la classe MotorPasAPas (importada)...")
    print("=====================================================\n")
    print(f"Totes les proves utilitzaran els pins GPIO BCM: {PINS_MOTOR_PAS_A_PAS}.")
    print("Assegura't que el teu motor pas a pas (i driver ULN2003) està correctament connectat a aquests pins (i alimentació!).\n")

    # TEST 1: Ús bàsic (moviments per graus i passos)
    print("--- TEST 1: Ús bàsic de MotorPasAPas (moviment relatiu) ---")
    try:
        with MotorPasAPas(
            nom="Motor_Principal",
            pins_in=PINS_MOTOR_PAS_A_PAS,
            passos_per_volta_motor=32,       # Per al 28BYJ-48
            reduccio_engranatge=64.0,       # Per al 28BYJ-48 (comunament 63.68)
            mode_passos='half'              # Mode 'half' step per defecte
        ) as motor1:
            print(f"\nConfiguració actual del {motor1.nom}:")
            print(f"  Pins: {motor1.pins_in}")
            print(f"  Mode: {motor1.mode_passos}")
            print(f"  Passos per volta completa: {motor1.passos_per_volta}")
            print(f"  Posició inicial: {motor1.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("\nPremeu Intro per moure 90 graus ENDAVANT a 60 deg/s...")
            motor1.moure_n_graus(90, MotorPasAPas.DIRECCIO_ENDAVANT, velocitat_graus_per_segon=60)
            print(f"Posició actual després de 90°: {motor1.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("Premeu Intro per moure 45 graus ENRERE a 90 deg/s...")
            motor1.moure_n_graus(45, MotorPasAPas.DIRECCIO_ENRERE, velocitat_graus_per_segon=90)
            print(f"Posició actual després de -45°: {motor1.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("Premeu Intro per moure 500 passos ENDAVANT a 120 deg/s...")
            motor1.moure_n_passos(500, MotorPasAPas.DIRECCIO_ENDAVANT, velocitat_graus_per_segon=120)
            print(f"Posició actual després de 500 passos: {motor1.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("Premeu Intro per desenergitzar el motor (release)...")
            motor1.release_motor()

        print("Final del Test 1. El motor hauria d'estar desenergitzat i els pins netejats per __exit__.")
    except Exception as e:
        print(f"ERROR DURANT EL TEST 1: {e}")
    finally:
        # Aquesta neteja general és per si el `with` falla abans de la configuració completa
        # o si es vol una neteja addicional. Normalment la gestiona __exit__ o __del__.
        try:
            GPIO.cleanup(PINS_MOTOR_PAS_A_PAS)
        except RuntimeWarning:
            pass # Ignora si ja s'ha netejat
        except Exception:
            pass


    esperar_per_continuar("\nPremeu Intro per continuar amb el Test 2 (Calibratge i Moviment Absolut)...")
    print("----------------------------------------------------------------\n")

    # TEST 2: Calibratge i Moviment Absolut a Graus
    print("--- TEST 2: Calibratge i Moviment Absolut ---")
    try:
        with MotorPasAPas(
            nom="Motor_Absolut",
            pins_in=PINS_MOTOR_PAS_A_PAS, # Reutilitzem els mateixos pins
            passos_per_volta_motor=32,
            reduccio_engranatge=64.0,
            mode_passos='half'
        ) as motor2:
            print(f"\nConfiguració actual del {motor2.nom}:")
            print(f"  Posició inicial: {motor2.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("\nPremeu Intro per calibrar el motor (posant-lo a 0°)...")
            motor2.calibrar(passos_max_calibratge=motor2.passos_per_volta * 2, # Moure 2 voltes per assegurar el "zero"
                            direccio_calibratge=MotorPasAPas.DIRECCIO_ENRERE,
                            velocitat_graus_per_segon=45)
            print(f"Posició després de calibratge: {motor2.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("\nPremeu Intro per moure a 90° (absolut)...")
            motor2.moure_a_graus(90, velocitat_graus_per_segon=75)
            print(f"Posició actual: {motor2.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("Premeu Intro per moure a 270° (absolut)...")
            motor2.moure_a_graus(270, velocitat_graus_per_segon=75)
            print(f"Posició actual: {motor2.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("Premeu Intro per moure a 0° (absolut)...")
            motor2.moure_a_graus(0, velocitat_graus_per_segon=75)
            print(f"Posició actual: {motor2.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("Premeu Intro per moure a 360° (absolut - hauria de ser 0°)...")
            motor2.moure_a_graus(360, velocitat_graus_per_segon=75)
            print(f"Posició actual: {motor2.obtenir_posicio_graus():.2f}°")

            esperar_per_continuar("Premeu Intro per moure a -90° (absolut - hauria de ser 270°)...")
            motor2.moure_a_graus(-90, velocitat_graus_per_segon=75)
            print(f"Posició actual: {motor2.obtenir_posicio_graus():.2f}°")
            
            esperar_per_continuar("Premeu Intro per moure a 180° (absolut)...")
            motor2.moure_a_graus(180, velocitat_graus_per_segon=75)
            print(f"Posició actual: {motor2.obtenir_posicio_graus():.2f}°")


        print("Final del Test 2. El motor hauria d'estar desenergitzat i els pins netejats.")
    except Exception as e:
        print(f"ERROR DURANT EL TEST 2: {e}")
    finally:
        try:
            GPIO.cleanup(PINS_MOTOR_PAS_A_PAS)
        except RuntimeWarning:
            pass
        except Exception:
            pass

    esperar_per_continuar("\nPremeu Intro per continuar amb el Test 3 (Validació d'Errors)...")
    print("------------------------------------------------------------------\n")

    # TEST 3: Validació de Paràmetres i Gestió d'Errors
    print("--- TEST 3: Validació de Paràmetres i Gestió d'Errors ---")

    # Test 3.1: Pins incorrectes
    print("\n[Test 3.1] Intentant inicialitzar amb pins invàlids:")
    try:
        MotorPasAPas(nom="Motor_PinsInvalid", pins_in=[1, 2, 3]) # Manca un pin
        print("ERROR: La creació amb pins invàlids hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA: {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    # Test 3.2: Passos per volta zero
    print("\n[Test 3.2] Intentant inicialitzar amb passos_per_volta_motor zero:")
    try:
        MotorPasAPas(nom="Motor_PassosZero", pins_in=PINS_MOTOR_PAS_A_PAS, passos_per_volta_motor=0)
        print("ERROR: La creació amb passos_per_volta_motor zero hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA: {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    # Test 3.3: Mode de passos invàlid
    print("\n[Test 3.3] Intentant inicialitzar amb mode_passos invàlid:")
    try:
        MotorPasAPas(nom="Motor_ModeInvalid", pins_in=PINS_MOTOR_PAS_A_PAS, mode_passos='quarter')
        print("ERROR: La creació amb mode_passos invàlid hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA: {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    # Test 3.4: Intentar moure sense setup (fora del context 'with')
    print("\n[Test 3.4] Intentant moure sense haver configurat els pins (fora de 'with'):")
    motor_no_setup = MotorPasAPas(nom="Motor_NoSetup", pins_in=PINS_MOTOR_PAS_A_PAS)
    try:
        motor_no_setup.moure_n_graus(90, MotorPasAPas.DIRECCIO_ENDAVANT)
        print("ERROR: El moviment sense setup hauria d'haver fallat (o almenys mostrat un missatge).")
    except Exception as e:
        print(f"ERROR INESPERAT (potser la classe no ho gestiona com a excepció): {e}")
    # Netegem manualment l'objecte creat aquí per assegurar la crida a __del__
    del motor_no_setup
    time.sleep(0.5) # Donem temps al GC si cal

    print("Final del Test 3.")

    esperar_per_continuar("\nPremeu Intro per continuar amb el Test 4 (__del__ Safeguard)...")
    print("------------------------------------------------------------------\n")

    # TEST 4: Demostració de __del__ (salvaguarda si no s'usa 'with')
    print("--- TEST 4: Demostració de __del__ (NO RECOMANAT, SEMPRE USAR 'with') ---")
    motor_no_with = None
    try:
        print("Creant MotorPasAPas SENSE usar 'with'...")
        # NOTA: Per veure __del__ funcionant, hem de cridar setup_gpio() explícitament
        # ja que __enter__ no es crida sense 'with'.
        motor_no_with = MotorPasAPas(nom="Motor_NoWith", pins_in=PINS_MOTOR_PAS_A_PAS)
        motor_no_with.setup_gpio() # Cal configurar explícitament per activar _is_setup

        esperar_per_continuar("Premeu Intro per eliminar l'objecte i veure __del__ (si es va activar setup_gpio)...")
        if motor_no_with._is_setup:
            print("L'objecte ha configurat els pins. Eliminant objecte per forçar __del__.")
        del motor_no_with
        print("Objecte 'motor_no_with' eliminat. Hauries de veure el missatge de __del__ si es va cridar.")
        time.sleep(1) # Donem un petit temps per si el GC actua
    except Exception as e:
        print(f"ERROR DURANT EL TEST 4: {e}")
    finally:
        print("Final del Test 4.")
        # Neteja global addicional per al pin del test 4, per si de cas
        try:
            GPIO.cleanup(PINS_MOTOR_PAS_A_PAS)
        except RuntimeWarning:
            pass # Ignorem errors si ja està netejat
        except Exception:
            pass

    print("\n=========================================")
    print("--- Neteja final de GPIO (global) ---")
    try:
        # Neteja tots els pins GPIO que s'hagin configurat durant l'execució.
        # Això és un salvavides final, ja que els blocs 'with' ja netegen els seus pins.
        GPIO.cleanup()
        print("Neteja global de GPIO realitzada.")
    except Exception as e:
        print(f"Error durant la neteja global de GPIO: {e}")

    print("\nProves finalitzades.")
    esperar_per_continuar("Premeu Intro per sortir del programa de proves.")
