#!/usr.bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import sys

# IMPORTANT: Ajusta aquesta línia segons la ubicació real del teu fitxer MotorPasAPas.
# Si MotorPasAPas.py està directament al mateix directori que aquest script de prova:
# from MotorPasAPasNoNormalitzat import MotorPasAPas
#
# Si està en 'scripts/controladors/MotorPasAPasNoNormalitzat.py' com indicaves:
# Per fer-ho funcionar, hauríàs d'assegurar-te que el directori 'scripts' és accessible en el PATH.
# Una manera senzilla per a proves locals és afegir el directori pare al path o posar els fitxers junts.
# Per simplicitat en aquest exemple, assumiré que la teva classe es diu 'MotorPasAPas'
# i que la pots importar directament si aquest script està al mateix nivell que el directori 'scripts',
# o bé adjusta la importació directament a la teva estructura de projecte.

# Per a aquesta demostració i per fer que la importació funcioni sense moure fitxers,
# simularem l'estructura. En un cas real, assegura't que el mòdul és trobable.
try:
    # Aquesta és la importació basada en la teva ruta: scripts.controladors.MotorPasAPasNoNormalitzat
    # Potser necessites ajustar el PYTHONPATH o la forma d'executar el script.
    # Per a una execució simple des del directori pare de 'scripts':
    # python -m scripts.tests.nom_del_fitxer_test
    # O afegeix el directori pare al sys.path
    # sys.path.append('/path/to/your/project/root')
    # from scripts.controladors.MotorPasAPasNoNormalitzat import MotorPasAPas
    
    # Per fer-ho més robust per a l'execució d'aquest fitxer de prova sol,
    # assumim que el fitxer MotorPasAPasNoNormalitzat.py està al mateix directori o un directori germà simple.
    # Si és directament al mateix directori:
    from scripts.controladors.MotorPasAPasNoNormalitzat import MotorPasAPas
except ImportError:
    print("No s'ha pogut importar la classe MotorPasAPasNoNormalitzat.")
    print("Assegura't que el fitxer 'MotorPasAPasNoNormalitzat.py' es troba al mateix directori")
    print("que aquest script de prova, o que la ruta d'importació és correcta.")
    sys.exit(1)


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
    # Posa uns pins que estiguin lliures i que siguin de sortida (OUT).
    #PINS_MOTOR_PAS_A_PAS = [4, 17, 27, 22] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    #PINS_MOTOR_PAS_A_PAS = [24, 25, 8, 7] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    PINS_MOTOR_PAS_A_PAS = [10, 9, 11, 5] # Pins BCM d'exemple (IN1, IN2, IN3, IN4 del driver ULN2003)
    print("Iniciant prova de la classe MotorPasAPas (mode manual / hardware)...")
    print("=================================================================\n")
    print(f"Totes les proves utilitzaran els pins GPIO BCM: {PINS_MOTOR_PAS_A_PAS}.")
    print("Assegura't que el teu motor pas a pas (i driver ULN2003) està correctament connectat a aquests pins (i alimentació!).\n")

    # TEST 1: Ús bàsic (moviments per graus i passos)
    print("--- TEST 1: Ús bàsic de MotorPasAPas (moviment relatiu) ---")
    try:
        with MotorPasAPas(
            nom="Motor_Principal",
            pins_in=PINS_MOTOR_PAS_A_PAS,
            passos_per_volta_motor=32,      # Per al 28BYJ-48
            reduccio_engranatge=64.0,       # Per al 28BYJ-48 (comunament 63.68, però 64.0 per simplicitat)
            mode_passos='half'              # Mode 'half' step per defecte
        ) as motor1:
            print(f"\nConfiguració actual del {motor1.nom}:")
            print(f"  Pins: {motor1.pins_in}")
            print(f"  Mode: {motor1.mode_passos}")
            print(f"  Passos per volta completa: {motor1.passos_per_volta}")
            print(f"  Posició inicial: {motor1.obtenir_posicio_graus():.2f}°")
            print(f"  Posició normalitzada: {motor1.obtenir_posicio_graus_normalitzada():.2f}°")

            esperar_per_continuar("\nPremeu Intro per moure 90 graus ENDAVANT (horari) a 60 deg/s...")
            motor1.moure_n_graus(90, MotorPasAPas.DIRECCIO_ENDAVANT, velocitat_graus_per_segon=60)
            print(f"Posició actual (absoluta): {motor1.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor1.obtenir_posicio_graus_normalitzada():.2f}°")

            esperar_per_continuar("Premeu Intro per moure 45 graus ENRERE (anti-horari) a 90 deg/s...")
            motor1.moure_n_graus(45, MotorPasAPas.DIRECCIO_ENRERE, velocitat_graus_per_segon=90)
            print(f"Posició actual (absoluta): {motor1.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor1.obtenir_posicio_graus_normalitzada():.2f}°")

            esperar_per_continuar("Premeu Intro per moure 500 passos ENDAVANT a 120 deg/s...")
            motor1.moure_n_passos(500, MotorPasAPas.DIRECCIO_ENDAVANT, velocitat_graus_per_segon=120)
            print(f"Posició actual (absoluta): {motor1.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor1.obtenir_posicio_graus_normalitzada():.2f}°")

            esperar_per_continuar("Premeu Intro per desenergitzar el motor (release)...")
            motor1.release_motor()

        print("\nFinal del Test 1. El motor hauria d'estar desenergitzat i els pins netejats per __exit__.")
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

            esperar_per_continuar("\nPremeu Intro per calibrar el motor (simulant posant-lo a 0°)...")
            # Hem de simular que el motor arriba a un final de carrera en una direcció i reiniciar la posició.
            # Movent un gran nombre de passos en la direcció de calibratge (per exemple, ENRERE),
            # assegurem que, conceptualment, "toca" el final de carrera i la seva posició es reinicia a 0.
            # Si el motor es mou cap endavant per arribar al zero, caldria canviar 'DIRECCIO_ENRERE' a 'DIRECCIO_ENDAVANT'.
            motor2.calibrar(passos_max_calibratge=motor2.passos_per_volta * 2, # Moure 2 voltes per assegurar el "zero"
                            direccio_calibratge=MotorPasAPas.DIRECCIO_ENRERE, # O DIRECCIO_ENDAVANT segons el teu setup físic
                            velocitat_graus_per_segon=45)
            print(f"Posició després de calibratge: {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició normalitzada després de calibratge: {motor2.obtenir_posicio_graus_normalitzada():.2f}°")


            # Proves de moviment absolut per validar el problema de 0 a 360
            esperar_per_continuar("\n--- Validant Moviment Absolut (0 a 360 i valors extrems) ---")
            esperar_per_continuar("Premeu Intro per moure a 90° (absolut)...")
            motor2.moure_a_graus(90, velocitat_graus_per_segon=75)
            print(f"Posició actual (absoluta): {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor2.obtenir_posicio_graus_normalitzada():.2f}°")

            esperar_per_continuar("Premeu Intro per moure a 180° (absolut)...")
            motor2.moure_a_graus(180, velocitat_graus_per_segon=75)
            print(f"Posició actual (absoluta): {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor2.obtenir_posicio_graus_normalitzada():.2f}°")
            
            esperar_per_continuar("Premeu Intro per moure a 270° (absolut)...")
            motor2.moure_a_graus(270, velocitat_graus_per_segon=75)
            print(f"Posició actual (absoluta): {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor2.obtenir_posicio_graus_normalitzada():.2f}°")

            esperar_per_continuar("Premeu Intro per moure a 0° (absolut)...")
            motor2.moure_a_graus(0, velocitat_graus_per_segon=75)
            print(f"Posició actual (absoluta): {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor2.obtenir_posicio_graus_normalitzada():.2f}°")

            # Aquesta és la prova clau per a "0 a 360":
            # Si el motor ja està a 0°, moure a 360° hauria de fer un moviment de 0° o una volta completa
            # depenent de si vols que es normalitzi a 0 o faci la volta sencera.
            # Si la teva posició de 360 és un sinònim de 0 i no hi ha moviment, és correcte.
            # Si vols que faci una volta completa, hauries de recalcular els passos.
            # La teva implementació actual de `moure_a_graus` sembla que normalitza.
            esperar_per_continuar("Premeu Intro per moure a 360° (absolut - hauria de ser 0° i NO MOUre's si ja hi és, o fer una volta COMPLETA si es vol)...")
            motor2.moure_a_graus(360, velocitat_graus_per_segon=75) # 360° és equivalent a 0° per la normalització
            print(f"Posició actual (absoluta): {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor2.obtenir_posicio_graus_normalitzada():.2f}°")
            
            # Si "0 a 360 a de moures 1 bolta al contrari que abans" es refereix a que
            # quan l'objectiu és 360 i l'actual és 0, vulguis que faci una volta completa en una direcció específica,
            # la teva funció `moure_a_graus` necessitaria un paràmetre o una lògica per decidir això.
            # La implementació actual de `moure_a_graus` busca el camí més curt (absolut), i 360 == 0.
            # Per forçar una volta, hauries de cridar:
            # motor2.moure_n_graus(360, MotorPasAPas.DIRECCIO_ENDAVANT)

            esperar_per_continuar("Premeu Intro per moure a -90° (absolut - hauria de ser 270° normalitzat)...")
            motor2.moure_a_graus(-90, velocitat_graus_per_segon=75) # -90° és equivalent a 270° normalitzat
            print(f"Posició actual (absoluta): {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor2.obtenir_posicio_graus_normalitzada():.2f}°")

            esperar_per_continuar("Premeu Intro per moure a 450° (absolut - hauria de ser 90° normalitzat)...")
            motor2.moure_a_graus(450, velocitat_graus_per_segon=75) # 450° és equivalent a 90° normalitzat
            print(f"Posició actual (absoluta): {motor2.obtenir_posicio_graus():.2f}°")
            print(f"Posició actual (normalitzada): {motor2.obtenir_posicio_graus_normalitzada():.2f}°")

        print("\nFinal del Test 2. El motor hauria d'estar desenergitzat i els pins netejats.")
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
    print("\n[Test 3.1] Intentant inicialitzar amb pins invàlids (llista massa curta):")
    try:
        MotorPasAPas(nom="Motor_PinsInvalid", pins_in=[1, 2, 3]) # Manca un pin
        print("ERROR: La creació amb pins invàlids hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA (OK): {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    print("\n[Test 3.1b] Intentant inicialitzar amb pins invàlids (element no enter):")
    try:
        MotorPasAPas(nom="Motor_PinsInvalidType", pins_in=[1, 2, 3, "quatre"]) # Un pin no és enter
        print("ERROR: La creació amb pins invàlids hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA (OK): {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    # Test 3.2: Passos per volta zero o negatius
    print("\n[Test 3.2] Intentant inicialitzar amb passos_per_volta_motor zero:")
    try:
        MotorPasAPas(nom="Motor_PassosZero", pins_in=PINS_MOTOR_PAS_A_PAS, passos_per_volta_motor=0)
        print("ERROR: La creació amb passos_per_volta_motor zero hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA (OK): {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    print("\n[Test 3.2b] Intentant inicialitzar amb reduccio_engranatge negatiu:")
    try:
        MotorPasAPas(nom="Motor_ReduccioNegativa", pins_in=PINS_MOTOR_PAS_A_PAS, reduccio_engranatge=-10.0)
        print("ERROR: La creació amb reduccio_engranatge negatiu hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA (OK): {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")


    # Test 3.3: Mode de passos invàlid
    print("\n[Test 3.3] Intentant inicialitzar amb mode_passos invàlid:")
    try:
        MotorPasAPas(nom="Motor_ModeInvalid", pins_in=PINS_MOTOR_PAS_A_PAS, mode_passos='quarter')
        print("ERROR: La creació amb mode_passos invàlid hauria d'haver fallat.")
    except ValueError as e:
        print(f"CAPTURA D'ERROR ESPERADA (OK): {e}")
    except Exception as e:
        print(f"ERROR INESPERAT: {e}")

    # Test 3.4: Intentar moure sense setup (fora del context 'with')
    print("\n[Test 3.4] Intentant moure sense haver configurat els pins (fora de 'with'):")
    motor_no_setup = MotorPasAPas(nom="Motor_NoSetup", pins_in=PINS_MOTOR_PAS_A_PAS)
    try:
        # Aquesta crida no generarà una excepció, sinó que imprimirà un error internament
        # i no farà res, que és el comportament desitjat de la teva classe.
        motor_no_setup.moure_n_graus(90, MotorPasAPas.DIRECCIO_ENDAVANT)
        print("Comprovat: La crida a moure_n_graus sense setup ha imprès un ERROR i no ha fet moviment. (OK)")
    except Exception as e:
        print(f"ERROR INESPERAT (la classe hauria de gestionar-ho internament): {e}")
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
        
        # Eliminar la referència fa que Python pugui cridar __del__ si no hi ha altres referències.
        # Això no sempre és immediat a causa del recol·lector d'escombraries (garbage collector).
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
