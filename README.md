# Domibot

# Table of Contents
   * [What is Domibot?](#what-is-domibot)
   * [Requirements](#requirements)
   * [Documentation](#documentation)
   * [How to use](#how-to-use)
   * [Authors](#authors)

## What is Domibot?

Domibot is a robot made for help people to play domino without the use of hands. With the intention of helping those who can't do it by themselves.

In this github you will find:
- A complete simulation with Coppelia
- Adaptation of SW to run into a raspberryPI

## Requirements

For running any code:

  - [Python 3.13.x](https://www.python.org/)
     
  - [NumPy](https://numpy.org/)
     
  - [SciPy](https://scipy.org/)

  - [CV2](https://opencv.org/)

  - [gTTS](https://pypi.org/project/gTTS/)

  - [speech\_recognition](https://pypi.org/project/SpeechRecognition/)

  - [pygame](https://www.google.com/search?q=https://www.pygame.org/wiki/About)

  - [pydub](https://pypi.org/project/pydub/)

Additionally to run the code in raspberrypi:

  - [picamera2](https://pypi.org/project/picamera2/)

  - [sounddevice](https://python-sounddevice.readthedocs.io/en/latest/)

  - [adafruit-circuitpython-tpa2016](https://pypi.org/project/adafruit-circuitpython-tpa2016/)

  - [adafruit-blinka](https://pypi.org/project/Adafruit-Blinka/)

  - [RPi.GPIO](https://pypi.org/project/RPi.GPIO/)

## Documentation

Code is distributed through three main points:

- [Main Code (main.py)](./main.py):
 This is the python file to run the entire software, in simulation or real hardware.
 It asks at the beginning the type of run (simulation or hardware) and executes all the program until the game ends.

- [Virtual_Controllers Folder](./Virtual_Controllers/):
 This folder contains all the classes and files of the program needed to run both on HW and on only simulation type.

- [Hardware_Controllers Folder](./Hardware_Controllers/):
 This folder contains all the code and information to send and receive data to our rasberryPi, and to execute actions like moving the motors. 
 For documentation and more information use [Hardware Information Folder](./Hardware_Information/)

## How to use

1. Clone this repo.

   ```terminal
   git clone https://github.com/LinceRojo/Domibot.git
   ```

If run on simulation:

2. Open and run [coppelia file](./Coppelia/Domibot.ttt)

3. Execute [main.py](./main.py) and select simulation mode

If run on raspberry:

2. Prepare and build the robot with the same hardware used, or adapt the code to your needs

3. Export all the code into raspberryPi

4. Access via SSH to the raspberryPi

5. Execute [main.py](./main.py) and select hardware mode 

## Authors

- [Villar Casino, Raúl](https://github.com/LinceRojo)
- [Rafecas Rubió, Albert](https://github.com/bertRR)
- [Molero Santucho, Joel](https://github.com/joel-molero)
- [Lozano Amores, Aaron](https://github.com/AaronLozanoAmores)
