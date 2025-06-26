import RPi.GPIO as GPIO
import time

# Defineix el pin GPIO de la Raspberry Pi al qual està connectat el pin de SENYAL del relé
# En aquest cas, GPIO18, que correspon al Pin físic 12 de la Raspberry Pi.
RELAY_PIN = 18

# Configura el mode dels pins de la Raspberry Pi
# GPIO.BCM significa que utilitzem la numeració dels pins GPIO (ex: GPIO18)
# GPIO.BOARD utilitzaria la numeració física dels pins (ex: 12)
GPIO.setmode(GPIO.BCM)

# Configura el pin del relé com a sortida
GPIO.setup(RELAY_PIN, GPIO.OUT)

print("Iniciant prova de l'electroimant amb relé...")
print("Premeu Ctrl+C per aturar el programa.")

try:
    while True:
        # Activa el relé (això tanca el circuit de l'electroimant)
        # Normalment, per a un relé, HIGH significa activat
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        print("Electroimant: ON")
        input("temps? ")
        # Desactiva el relé (això obre el circuit de l'electroimant)
        GPIO.output(RELAY_PIN, GPIO.LOW)
        print("Electroimant: OFF")
        input("temps? ")
except KeyboardInterrupt:
    # Quan es prem Ctrl+C, desactiva el relé i neteja els pins GPIO
    GPIO.output(RELAY_PIN, GPIO.LOW) # Assegura't que l'electroimant s'apaga
    GPIO.cleanup()                   # Allibera els pins GPIO
    print("\nPrograma aturat. Relé desactivat, electroimant apagat.")
except Exception as e:
    print(f"S'ha produït un error: {e}")
    GPIO.cleanup() # Neteja els pins en cas d'error
