#!/usr.bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO 
from scripts.controladors.Servomotor import Servomotor 

# Funció per esperar la interacció de l'usuari
def esperar_per_continuar(missatge="Premeu Intro per continuar..."):
    """
    Pausa l'execució del programa fins que l'usuari premeu Intro.
    """
    input(missatge)

# ----------- Lògica de prova -----------
if __name__ == "__main__":
    # *** IMPORTANT: Aquest és l'ÚNIC pin que necessites per a totes les proves de moviment! ***
    # Utilitza la numeració BCM. GPIO12 correspon al pin físic 32 a la Raspberry Pi.
    PIN_UNICO_SERVO = 12  # Pin per a TOTS els tests de moviment (Numeració BCM)

    print("Iniciant prova de la classe Servomotor (importada)...")
    print("=====================================================\n")
    print(f"Totes les proves de moviment utilitzaran el pin GPIO BCM {PIN_UNICO_SERVO}.")
    print("Assegura't que el teu servomotor està correctament connectat a aquest pin (i alimentació!).\n")

    # TEST 1: Ús bàsic amb un servomotor SG90 (paràmetres de la teva imatge: 5%-10% DC)
    print("--- TEST 1: Ús bàsic de Servomotor SG90 (0-180° amb 5%-10% DC) ---")
    try:
        with Servomotor(
            nom_servomotor="Servo_SG90_Basic",
            pin_gpio=PIN_UNICO_SERVO, # Utilitzem el pin únic
            pwm_frequency=50, 
            duty_cycle_min=2.190, 
            duty_cycle_max=12.290 
        ) as servo1:
            print("Configuració actual del Servo_SG90_Basic:")
            print(servo1.get_current_configuration())

            esperar_per_continuar("\nPremeu Intro per moure el servo a 0°...")
            servo1.move_to_angle(0)

            esperar_per_continuar("Premeu Intro per moure el servo a 90°...")
            servo1.move_to_angle(90)

            esperar_per_continuar("Premeu Intro per moure el servo a 180°...")
            servo1.move_to_angle(180)

            esperar_per_continuar("Premeu Intro per tornar el servo a 0°...")
            servo1.move_to_angle(0)

        print("Final del Test 1. El pin hauria d'estar netejat per __exit__.")
    except Exception as e:
        print(f"ERROR DURANT EL TEST 1: {e}")

    esperar_per_continuar("\nPremeu Intro per continuar amb el Test 2 (Rang Operacional)...")
    print("----------------------------------------------------------------\n")

    # TEST 2: Servomotor amb rang d'angles operacionals limitat (e.g., 45° a 135°)
    print("--- TEST 2: Servomotor amb Rang Operacional Limitado (45°-135°) ---")
    try:
        with Servomotor(
            nom_servomotor="Servo_Limitat",
            pin_gpio=PIN_UNICO_SERVO, # Utilitzem el pin únic
            angle_min_operational=45,
            angle_max_operational=135,
            duty_cycle_min=2.190, 
            duty_cycle_max=12.290 
        ) as servo2:
            print("Configuració actual del Servo_Limitat:")
            print(servo2.get_current_configuration())

            esperar_per_continuar("\nPremeu Intro per moure el servo a 0° (hauria d'anar a 45°)...")
            servo2.move_to_angle(0) # Hauria de ser clamped a 45°

            esperar_per_continuar("Premeu Intro per moure el servo a 90°...")
            servo2.move_to_angle(90)

            esperar_per_continuar("Premeu Intro per moure el servo a 180° (hauria d'anar a 135°)...")
            servo2.move_to_angle(180) # Hauria de ser clamped a 135°

            esperar_per_continuar("Premeu Intro per moure el servo a 45° (límit inferior)...")
            servo2.move_to_angle(45)

            esperar_per_continuar("Premeu Intro per moure el servo a 135° (límit superior)...")
            servo2.move_to_angle(135)

        print("Final del Test 2. El pin hauria d'estar netejat per __exit__.")
    except Exception as e:
        print(f"ERROR DURANT EL TEST 2: {e}")

    esperar_per_continuar("\nPremeu Intro per continuar amb el Test 3 (Validació d'Errors)...")
    print("------------------------------------------------------------------\n")

    # TEST 3: Validació de paràmetres i gestió d'errors en la inicialització
    print("--- TEST 3: Validació de Paràmetres i Gestió d'Errors ---")
    print("Aquests tests provaran errors en la configuració de la classe, no mouran el servo.")

    # Test 3.1: Freqüència PWM invàlida
    print("\n[Test 3.1] Intentant inicialitzar amb freqüència PWM zero:")
    try:
        Servomotor(nom_servomotor="Servo_FreqInvalida", pin_gpio=PIN_UNICO_SERVO, pwm_frequency=0)
        print("ERROR: La creació amb freqüència zero hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA: {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    # Test 3.2: Rang d'angles operacionals invàlid (min > max)
    print("\n[Test 3.2] Intentant inicialitzar amb angle_min_operational > angle_max_operational:")
    try:
        Servomotor(nom_servomotor="Servo_RangAngleInvalida", pin_gpio=PIN_UNICO_SERVO,
                   angle_min_operational=100, angle_max_operational=80)
        print("ERROR: La creació amb rang d'angle invàlid hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA: {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    # Test 3.3: Rang de cicle de treball operacional invàlid (min >= max)
    print("\n[Test 3.3] Intentant inicialitzar amb duty_cycle_min >= duty_cycle_max:")
    try:
        Servomotor(nom_servomotor="Servo_RangDCInvalida", pin_gpio=PIN_UNICO_SERVO,
                   duty_cycle_min=5.0, duty_cycle_max=5.0)
        print("ERROR: La creació amb rang de cicle de treball invàlid hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA: {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    print("Final del Test 3.")

    esperar_per_continuar("\nPremeu Intro per continuar amb el Test 4 (__del__ Safeguard)...")
    print("------------------------------------------------------------------\n")

    # TEST 4: Demostració de __del__ (salvaguarda si no s'usa 'with')
    print("--- TEST 4: Demostració de __del__ (NO RECOMANAT, SEMPRE USAR 'with') ---")
    print(f"Controlant el servomotor al pin GPIO {PIN_UNICO_SERVO}.")
    servo_no_with = None
    try:
        print("Creant Servomotor SENSE usar 'with'...")
        servo_no_with = Servomotor(nom_servomotor="Servo_NoWith", pin_gpio=PIN_UNICO_SERVO)
        
        # Intentem moure el servo sense haver entrat al context (hauria de donar error)
        print("\nIntentant moure el servo abans d'entrar al context (hauria de mostrar ERROR):")
        servo_no_with.move_to_angle(90) # Això hauria de fallar i imprimir un error

        esperar_per_continuar("Premeu Intro per forçar la destrucció de l'objecte i veure __del__ (si es va inicialitzar correctament)...")
        # El test de __del__ és delicat i es basa en com Python gestiona la memòria.
        # Aquí, si l'objecte es va crear (sense que una excepció en __init__ el bloquegés),
        # intentem aturar el PWM i netejar el pin.
        if servo_no_with._initialized and servo_no_with._pwm: 
            print("Forçant aturada de PWM i neteja de GPIO (manualment, ja que no estem en 'with').")
            servo_no_with._pwm.stop()
            GPIO.cleanup(servo_no_with._pin_gpio)
            servo_no_with._initialized = False
        
        # Eliminar explícitament l'objecte per forçar la crida a __del__
        # Nota: Python pot no cridar __del__ immediatament si hi ha referències o si el GC no actua.
        del servo_no_with
        print("Objecte 'servo_no_with' eliminat. Hauries de veure el missatge de __del__ si es va cridar.")
        time.sleep(1) # Donem un petit temps per si el GC actua
    except Exception as e:
        print(f"ERROR DURANT EL TEST 4: {e}")
    finally:
        print("Final del Test 4.")
        # Neteja global addicional per al pin del test 4, per si de cas
        try:
            GPIO.cleanup(PIN_UNICO_SERVO)
        except Exception:
            pass # Ignorem errors si ja està netejat

    print("\n=========================================")
    print("--- Neteja final de GPIO (global) ---")
    try:
        # Neteja tots els pins GPIO que s'hagin configurat durant l'execució
        GPIO.cleanup()
        print("Neteja global de GPIO realitzada.")
    except Exception as e:
        print(f"Error durant la neteja global de GPIO: {e}")

    print("\nProves finalitzades.")
    esperar_per_continuar("Premeu Intro per sortir del programa de proves.")
