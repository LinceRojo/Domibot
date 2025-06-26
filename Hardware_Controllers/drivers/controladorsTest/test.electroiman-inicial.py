#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO # Encara necessari per al GPIO.cleanup() global al final
from scripts.controladors.Electroiman import Electroiman # Importem la classe des de l'altre fitxer

# Funció per esperar la interacció de l'usuari
def esperar_per_continuar(missatge="Premeu Intro per continuar..."):
    """
    Pausa l'execució del programa fins que l'usuari premeu Intro.
    """
    input(missatge)

# ----------- Lògica de prova -----------
if __name__ == "__main__":
    # *** IMPORTANT: Canvia aquests pins als que vulguis utilitzar i siguin segurs! ***
    PIN_ELECTROIMAN_TEST1 = 26  # Pin per al Test 1 (Numeració BCM)
    PIN_ELECTROIMAN_TEST2 = 26  # Pin per al Test 2 (Numeració BCM)
    PIN_REUTILITZABLE_TEST4 = 26 # Pin per al Test 4 (Numeració BCM)
    PIN_FALLA_TEST3 = 99 # Pin invàlid per provar la gestió d'errors de configuració

    print("Iniciant prova de la classe Electroiman (importada)...")
    print("=====================================================\n")

    # Test 1: Creació, activació, desactivació i neteja bàsica
    print("--- Test 1: Ús bàsic ---")
    electroiman1 = None # Inicialitzem a None
    try:
        print(f"Intentant inicialitzar Electroiman al pin {PIN_ELECTROIMAN_TEST1}")
        electroiman1 = Electroiman(PIN_ELECTROIMAN_TEST1)
        print(f"Estat inicial: {'Actiu' if electroiman1.estat_actiu() else 'Inactiu'}")

        esperar_per_continuar("\nPremeu Intro per activar l'electroimant del Test 1...")
        print("\nActivant electroimant...")
        if electroiman1.activar():
            print("Activació sembla exitosa des del test.")
        else:
            print("Activació sembla haver fallat des del test.")
        print(f"Estat després d'activar: {'Actiu' if electroiman1.estat_actiu() else 'Inactiu'}")
        print("L'electroimant hauria d'estar actiu. Premeu Intro per continuar.")
        esperar_per_continuar() # Espera fins que l'usuari premeu Intro

        print("\nDesactivant electroimant...")
        if electroiman1.desactivar():
            print("Desactivació sembla exitosa des del test.")
        else:
            print("Desactivació sembla haver fallat des del test.")
        print(f"Estat després de desactivar: {'Actiu' if electroiman1.estat_actiu() else 'Inactiu'}")
        esperar_per_continuar("Premeu Intro per finalitzar el Test 1...")

    except Exception as e:
        print(f"ERROR DURANT EL TEST 1: {e}")
    finally:
        if electroiman1:
            print("Eliminant explícitament l'objecte electroiman1 per activar __del__.")
            del electroiman1
        print("Final del Test 1. La neteja del pin s'hauria d'haver fet via __del__.")

    esperar_per_continuar("\nPremeu Intro per iniciar el Test 2...\n")

    # Test 2: Ús amb la sentència 'with'
    print("--- Test 2: Ús amb 'with' statement ---")
    try:
        print(f"Intentant inicialitzar Electroiman amb 'with' al pin {PIN_ELECTROIMAN_TEST2}")
        with Electroiman(PIN_ELECTROIMAN_TEST2) as electroiman_with:
            print(f"Estat inicial (dins de 'with'): {'Actiu' if electroiman_with.estat_actiu() else 'Inactiu'}")
            esperar_per_continuar("\nPremeu Intro per activar l'electroimant del Test 2...")

            print("\nActivant electroimant (dins de 'with')...")
            electroiman_with.activar()
            print(f"Estat després d'activar (dins de 'with'): {'Actiu' if electroiman_with.estat_actiu() else 'Inactiu'}")
            print("L'electroimant hauria d'estar actiu. Premeu Intro per continuar.")
            esperar_per_continuar()

            print("\nDesactivant electroimant (dins de 'with')...")
            electroiman_with.desactivar()
            print(f"Estat després de desactivar (dins de 'with'): {'Actiu' if electroiman_with.estat_actiu() else 'Inactiu'}")
            esperar_per_continuar("Premeu Intro per finalitzar el Test 2...")

        print("Fora del bloc 'with'. El pin hauria d'estar netejat per __exit__.")

    except Exception as e:
        print(f"ERROR DURANT EL TEST 2: {e}")
    finally:
        print("Final del Test 2.")

    esperar_per_continuar("\nPremeu Intro per iniciar el Test 3...\n")

    # Test 3: Intentar operacions amb un pin que podria fallar la configuració
    print("--- Test 3: Operacions amb pin potencialment problemàtic ---")
    electroiman_test_fail = None
    try:
        print(f"Intentant inicialitzar Electroiman amb un pin invàlid/problemàtic: {PIN_FALLA_TEST3}")
        electroiman_test_fail = Electroiman(PIN_FALLA_TEST3)

        if not electroiman_test_fail._construit:
            print(f"La configuració del pin {PIN_FALLA_TEST3} sembla haver fallat, com s'esperava.")
        else:
            print(f"ATENCIÓ: La configuració del pin {PIN_FALLA_TEST3} ha tingut èxit. Potser és un pin vàlid.")

        esperar_per_continuar("Premeu Intro per intentar activar l'electroimant (hauria de fallar si no està construït)...")
        electroiman_test_fail.activar()

        esperar_per_continuar("Premeu Intro per intentar desactivar l'electroimant (hauria de fallar si no està construït)...")
        electroiman_test_fail.desactivar()

    except Exception as e:
        print(f"ERROR INESPERAT DURANT EL TEST 3 amb pin {PIN_FALLA_TEST3}: {e}")
    finally:
        if electroiman_test_fail:
            print(f"Eliminant explícitament l'objecte electroiman_test_fail per activar __del__ (si es va crear).")
            del electroiman_test_fail
        print("Final del Test 3.")

    esperar_per_continuar("\nPremeu Intro per iniciar el Test 4...\n")

    # Test 4: Creació i destrucció múltiples per verificar la neteja i reutilització de pins
    print(f"--- Test 4: Reutilització del pin {PIN_REUTILITZABLE_TEST4} ---")
    try:
        print(f"Creant el primer electroimant (e1) al pin {PIN_REUTILITZABLE_TEST4}")
        e1 = Electroiman(PIN_REUTILITZABLE_TEST4)
        e1.activar()
        print(f"Estat e1: {'Actiu' if e1.estat_actiu() else 'Inactiu'}")
        esperar_per_continuar("Premeu Intro per desactivar e1 i alliberar el pin...")
        e1.desactivar()
        print(f"Estat e1: {'Actiu' if e1.estat_actiu() else 'Inactiu'}")

        print("Eliminant el primer objecte (e1) per alliberar el pin...")
        del e1
        esperar_per_continuar("Premeu Intro per crear el segon electroimant al mateix pin...")

        print(f"\nCreant el segon electroimant (e2) al MATEIX pin {PIN_REUTILITZABLE_TEST4}")
        e2 = Electroiman(PIN_REUTILITZABLE_TEST4)
        e2.activar()
        print(f"Estat e2: {'Actiu' if e2.estat_actiu() else 'Inactiu'}")
        esperar_per_continuar("Premeu Intro per desactivar e2...")
        e2.desactivar()
        print(f"Estat e2: {'Actiu' if e2.estat_actiu() else 'Inactiu'}")

        print("Eliminant el segon objecte (e2)...")
        del e2
        print("Prova de reutilització de pin completada amb èxit.")

    except Exception as e:
        print(f"ERROR DURANT EL TEST 4 (reutilització de pin {PIN_REUTILITZABLE_TEST4}): {e}")
    finally:
        print("Final del Test 4.")


    print("\n=========================================")
    print("--- Neteja final de GPIO (global) ---")
    try:
        GPIO.cleanup()
        print("Neteja global de GPIO realitzada.")
    except Exception as e:
        print(f"Error durant la neteja global de GPIO: {e}")

    print("\nProves finalitzades.")
    esperar_per_continuar("Premeu Intro per sortir del programa de proves.")
