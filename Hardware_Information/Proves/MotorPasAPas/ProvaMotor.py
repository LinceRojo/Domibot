#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Programa per controlar el motor pas a pas 28BYJ-48 amb driver ULN2003 a Raspberry Pi
# Basat en la seqüència de 8 passos per a mode de mig pas (half-step)
# Assegura't que la llibreria RPi.GPIO està instal·lada (normalment ja ho està a Raspberry Pi OS)

import RPi.GPIO as GPIO
import time
import atexit

# --- Definició de Pins i Seqüència ---

# Defineix els pins GPIO (numeració BCM) connectats a les entrades del driver ULN2003 (IN1 a IN4)
# Verifica les teves connexions físiques. Aquests pins corresponen als exemples comuns.
IN1 = 23 # Pin físic 16
IN2 = 24 # Pin físic 18
IN3 = 25 # Pin físic 22
IN4 = 8  # Pin físic 24
IN_PINS = [IN1, IN2, IN3, IN4]

# Defineix la seqüència de 8 passos per al motor 28BYJ-48 en mode de mig pas (half-step)
# Aquesta seqüència energitza els bobinats en l'ordre correcte per girar.
step_sequence = [
  [1, 0, 0, 0], # Pas 0
  [1, 1, 0, 0], # Pas 1
  [0, 1, 0, 0], # Pas 2
  [0, 1, 1, 0], # Pas 3
  [0, 0, 1, 0], # Pas 4
  [0, 0, 1, 1], # Pas 5
  [0, 0, 0, 1], # Pas 6
  [1, 0, 0, 1]  # Pas 7
]

# Nombre de passos (mig-passos) per a una revolució completa (360 graus) del motor 28BYJ-48
# Aquest motor té una reducció de 64:1 (aproximadament). El motor intern fa 32 passos per volta.
# 32 * 64 = 2048 mig-passos per volta completa amb aquesta seqüència de 8 passos.
HALF_STEPS_PER_REVOLUTION = 2048

# Variable global per mantenir la posició actual dins de la seqüència (de 0 a 7)
current_step = 0

# --- Funcions de Control ---

# Funció per configurar l'estat dels pins GPIO per a un pas concret
def set_step(pins_to_set):
    """Configura les sortides GPIO segons el patró de pins donat."""
    for pin_index in range(4):
        GPIO.output(IN_PINS[pin_index], pins_to_set[pin_index])

# Funció per alliberar el motor (desenergitzar totes les bobines)
# Això redueix el consum d'energia i permet moure el motor a mà.
def release_motor():
    """Posa tots els pins de control del motor a LOW per desenergitzar-lo."""
    print("Alliberant motor...")
    for pin in IN_PINS:
        GPIO.output(pin, GPIO.LOW)

# Funció per moure el motor un nombre determinat de passos en una direcció
def move_stepper(steps_to_move, direction, delay):
    """
    Mou el motor el nombre de passos indicat en la direcció especificada.

    Args:
        steps_to_move (int): Nombre de passos a moure.
        direction (str): Direcció del moviment ('forward' o 'backward').
        delay (float): Retard entre passos en segons.
    """
    global current_step # Accedeix a la variable global per mantenir la posició

    print(f"Movent {steps_to_move} passos cap a {direction}...")

    for _ in range(abs(steps_to_move)):
        if direction == "forward":
            # Avança al següent pas de la seqüència (circularment de 0 a 7)
            current_step = (current_step + 1) % 8
        elif direction == "backward":
            # Retrocedeix al pas anterior de la seqüència (circularment de 7 a 0)
            current_step = (current_step - 1) % 8
            # Python gestiona els mòduls negatius correctament per al wrap-around

        # Aplica el patró de voltatges del pas actual als pins GPIO
        set_step(step_sequence[current_step])

        # Espera el temps especificat abans del següent pas
        time.sleep(delay)

# --- Configuració GPIO i Bucle Principal ---

# Registra la funció release_motor per assegurar-se que els pins s'apaguen a la sortida
atexit.register(release_motor)

try:
    # Configuració inicial de GPIO
    GPIO.setmode(GPIO.BCM) # Utilitza la numeració BCM dels pins
    print("Configurant pins GPIO...")
    for pin in IN_PINS:
        GPIO.setup(pin, GPIO.OUT) # Configura els pins com a sortides
        GPIO.output(pin, GPIO.LOW) # Posa els pins a LOW per defecte

    # Defineix el retard entre mig-passos en segons.
    # Un valor més petit = més ràpid, però si és massa petit, el motor pot perdre passos.
    # Comença amb un valor segur i ajusta si cal. 0.002s (2ms) és un bon punt de partida.
    delay_between_steps = 0.002

    print("Iniciant cicle de prova. Prem Ctrl+C per sortir.")

    while True:
        # --- Prova 1: Girar una revolució en sentit horari ---
        print(f"\nGirant una revolució completa ({HALF_STEPS_PER_REVOLUTION} passos) endavant...")
        move_stepper(HALF_STEPS_PER_REVOLUTION, "forward", delay_between_steps)

        # Després de moure, pots alliberar el motor si vols estalviar energia
        # release_motor() # Descomenta aquesta línia si vols alliberar el motor entre moviments
        print("Pausa de 2 segons.")
        time.sleep(2) # Pausa de 2 segons

        # --- Prova 2: Girar una revolució en sentit antihorari ---
        print(f"\nGirant una revolució completa ({HALF_STEPS_PER_REVOLUTION} passos) enrere...")
        move_stepper(HALF_STEPS_PER_REVOLUTION, "backward", delay_between_steps)

        # Després de moure, pots alliberar el motor si vols estalviar energia
        # release_motor() # Descomenta aquesta línia si vols alliberar el motor entre moviments
        print("Pausa de 2 segons.")
        time.sleep(2) # Pausa de 2 segons

except KeyboardInterrupt:
    # Captura Ctrl+C per sortir netament
    print("\nInterrupció per l'usuari. Sortint...")

except Exception as e:
    # Captura qualsevol altre error inesperat
    print(f"\nS'ha produït un error inesperat: {e}")

finally:
    # Aquesta secció s'executa sempre, tant si hi ha error com si surts amb Ctrl+C.
    # Assegura que els pins GPIO es netegen i s'alliberen.
    print("Finalitzant. Netejant GPIO...")
    release_motor() # Assegura que els pins queden a LOW
    GPIO.cleanup()  # Allibera els recursos GPIO
    print("Neteja de GPIO completada.")
