"""
This Raspberry Pi code was developed by newbiely.com
This Raspberry Pi code is made available for public use without any restriction
For comprehensive instructions and wiring diagrams, please visit:
https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-28byj-48-stepper-motor-uln2003-driver
"""


import RPi.GPIO as GPIO
import time

# Define GPIO pins for ULN2003 driver
IN1 = 23
IN2 = 24
IN3 = 25
IN4 = 8

# Set GPIO mode and configure pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

# Define sequence for 28BYJ-48 stepper motor
seq = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
]

# Function to rotate the stepper motor one step
def step(delay, step_sequence):
        GPIO.output(IN1, step_sequence[0])
        GPIO.output(IN2, step_sequence[1])
        GPIO.output(IN3, step_sequence[2])
        GPIO.output(IN4, step_sequence[3])
        #print("Out:",step_sequence[0],step_sequence[1],step_sequence[2],step_sequence[3])
        time.sleep(delay)

try:
    # Set the delay between steps
    delay = 0.005

    while True:
        for i in range(4):
          step(delay, seq[i])

except KeyboardInterrupt:
    print("\nExiting the script.")

finally:
    # Clean up GPIO settings
    GPIO.cleanup()
  
