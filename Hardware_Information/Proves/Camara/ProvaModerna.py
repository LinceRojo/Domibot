#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Script per fer una foto amb libcamera i picamera2

from picamera2 import Picamera2
from time import sleep

# Inicialitza la càmera (utilitza libcamera)
picam2 = Picamera2()

# Configura la previsualització (opcional i no sempre visible en headless)
# Per a ús headless pur, potser no vols previsualització
# picam2.start_preview(Preview.QTGL) # Exemple, requereix entorn gràfic o VNC amb acceleració

# Per fer una pausa mentre la càmera s'inicialitza
print("Iniciant càmera... espera 2 segons.")
picam2.start() # Inicia la càmera sense previsualització
sleep(2) # Deixa temps perquè s'ajusti l'exposició automàtica

print("Fent foto...")
# Captura una imatge
picam2.capture_file("../test.jpg") # Guarda la foto en un fitxer

# Atura la càmera quan hagis acabat
picam2.stop()

print("Foto feta i guardada a /home/pi/Proves/test.jpg")
