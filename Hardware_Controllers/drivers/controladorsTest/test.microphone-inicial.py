#!/usr.bin/env python3
# -*- coding: utf-8 -*-

import time
import numpy as np
import sounddevice as sd
import soundfile as sf # Importem soundfile per guardar arxius d'àudio
import os # Per crear la carpeta de sortida

# Importem la classe Microphone des del fitxer separat
from scripts.controladors.Microphone import Microphone 

# Funció per esperar la interacció de l'usuari
def esperar_per_continuar(missatge="Premeu Intro per continuar..."):
    """
    Pausa l'execució del programa fins que l'usuari premeu Intro.
    """
    input(missatge)

# Funció de callback per al streaming (processa cada bloc d'àudio)
# Guardarem els blocs per comprovar-ho al final
stream_data_buffer = []
def streaming_callback(indata, frames, time_info, status):
    global stream_data_buffer
    if status:
        print(f"[CALLBACK WARNING]: {status}")
    # Afegim el bloc d'àudio al buffer. indata és un numpy array.
    stream_data_buffer.append(indata.copy()) # Cal fer una còpia perquè indata es reutilitza

# --- Main Test Execution ---
if __name__ == "__main__":
    print("Iniciant prova de la classe Microphone (amb fitxer separat)...")
    print("=============================================================\n")

    # Creem una carpeta específica per a les gravacions de la prova
    # El nom de la carpeta indica clarament que són arxius de test
    output_dir = "TestmMicrofonGravacions" 
    os.makedirs(output_dir, exist_ok=True) # Crea la carpeta si no existeix
    print(f"Les gravacions de prova es guardaran a la carpeta: '{output_dir}'\n")

    # TEST 1: Llistar dispositius d'entrada disponibles
    print("--- TEST 1: Llistant dispositius d'entrada ---")
    try:
        # Utilitzem un context manager fins i tot per llistar, per bones pràctiques
        # Samplerate i channels per defecte del constructor, no afecten el llistat.
        with Microphone(nom_microfon="Llistador") as mic: 
            dispositius = mic.list_input_devices()
            if not dispositius:
                print("[!] ATENCIÓ: No s'han trobat dispositius d'entrada. Potser no hi ha micròfons o drivers.")
                print("    Alguns tests podrien no funcionar correctament.")
            else:
                print(f"S'han trobat {len(dispositius)} dispositius d'entrada.")
    except Exception as e:
        print(f"ERROR durant el TEST 1 de llistat de dispositius: {e}")
    
    esperar_per_continuar("\nPremeu Intro per continuar amb la prova de gravació síncrona...")
    print("--------------------------------------------------\n")

    # TEST 2: Gravació síncrona (blocking)
    print("--- TEST 2: Gravació síncrona ---")
    # Ajustat: samplerate a 48000 Hz i channels a 1 per al micròfon mono SPH0645
    with Microphone(nom_microfon="MicSPH0645_Sinc", samplerate=48000, channels=1) as mic_sync:
        print("Preparat per gravar 3 segons d'àudio mono. Parla al micròfon!")
        audio_sincron = mic_sync.record_audio_data(duration=3)

        if audio_sincron:
            data, sr, ext, meta = audio_sincron
            print(f"Gravació síncrona exitosa! Mida de les dades: {data.shape}, Sample Rate: {sr}")
            
            # Guardar l'àudio a un fitxer .wav
            output_filename_sync = os.path.join(output_dir, "gravacio_sincrona_test.wav")
            try:
                # soundfile espera dades 1D o 2D amb el nombre de canals a la segona dimensió
                sf.write(output_filename_sync, data, sr)
                print(f"Àudio síncron guardat a '{output_filename_sync}'")
            except Exception as e:
                print(f"Error guardant l'àudio síncron: {e}")
        else:
            print("La gravació síncrona ha fallat o no ha retornat dades.")
    
    esperar_per_continuar("\nPremeu Intro per continuar amb la prova de streaming asíncron...")
    print("--------------------------------------------------\n")

    # TEST 3: Gravació en streaming asíncron
    print("--- TEST 3: Gravació en streaming (asíncron) ---")
    # Resetegem el buffer per a aquesta prova
    stream_data_buffer = []
    
    # Ajustat: samplerate a 48000 Hz i channels a 1 per al micròfon mono SPH0645
    with Microphone(nom_microfon="MicSPH0645_Stream", samplerate=48000, channels=1) as mic_stream:
        print("Iniciant streaming d'àudio mono. Estarà actiu durant 5 segons.")
        print("Parla al micròfon. Cada segon, es processaran dades.")
        mic_stream.start_streaming(callback_function=streaming_callback, blocksize=48000 // 2) # Processar 2 blocs per segon

        if mic_stream._stream and mic_stream._stream.active:
            print("Streaming actiu. Esperant 5 segons per recollir dades...")
            time.sleep(5) # Espera un temps mentre el callback recull dades
            mic_stream.stop_streaming()
            print("Streaming aturat.")
        else:
            print("El streaming no s'ha pogut iniciar.")

        if stream_data_buffer:
            total_samples = sum(len(block) for block in stream_data_buffer)
            print(f"Streaming exitós! S'han recollit {len(stream_data_buffer)} blocs d'àudio.")
            print(f"Total de mostres recollides en streaming: {total_samples}")
            
            # Unir les dades de streaming i guardar-les a un fitxer .wav
            full_stream_audio = np.concatenate(stream_data_buffer, axis=0)
            print(f"Forma de les dades de streaming concatenades: {full_stream_audio.shape}")

            output_filename_stream = os.path.join(output_dir, "gravacio_streaming_test.wav")
            try:
                sf.write(output_filename_stream, full_stream_audio, 48000) # El sample rate ja el tenim fixat
                print(f"Àudio de streaming guardat a '{output_filename_stream}'")
            except Exception as e:
                print(f"Error guardant l'àudio de streaming: {e}")
        else:
            print("No s'han recollit dades durant el streaming.")

    esperar_per_continuar("\nPremeu Intro per continuar amb les proves d'error...")
    print("--------------------------------------------------\n")

    # TEST 4: Gestió d'errors i casos límit
    print("--- TEST 4: Gestió d'errors ---")

    # Test 4.1: Samplerate invàlid
    print("\n[Test 4.1] Intentant inicialitzar amb samplerate invàlid (0):")
    try:
        with Microphone(samplerate=0) as mic_err:
            pass
    except ValueError as e:
        print(f"Capturat ERROR esperat: {e}")
    except Exception as e:
        print(f"Capturat ERROR inesperat: {e}")

    # Test 4.2: Channels invàlids
    print("\n[Test 4.2] Intentant inicialitzar amb canals invàlids (-1):")
    try:
        with Microphone(channels=-1) as mic_err:
            pass
    except ValueError as e:
        print(f"Capturat ERROR esperat: {e}")
    except Exception as e:
        print(f"Capturat ERROR inesperat: {e}")
    
    # Test 4.3: Intentar gravar síncronament mentre el streaming està actiu (no hauria de permetre-ho)
    print("\n[Test 4.3] Intentant gravar síncronament amb streaming actiu:")
    try:
        with Microphone(nom_microfon="MicErrorMix", samplerate=48000, channels=1) as mic_mix:
            mic_mix.start_streaming(callback_function=streaming_callback)
            print("Esperant 1 segon per assegurar que el streaming comenci...")
            time.sleep(1) 
            mic_mix.record_audio_data(duration=1) # Això hauria de fallar
            mic_mix.stop_streaming() # Netejar
    except Exception as e:
        print(f"Capturat ERROR inesperat durant la mescla de modes: {e}")


    esperar_per_continuar("\nPremeu Intro per finalitzar totes les proves...")
    print("--------------------------------------------------\n")

    print("=========================================")
    print("Totes les proves de la classe Microphone han finalitzat.")
    print("=========================================")
