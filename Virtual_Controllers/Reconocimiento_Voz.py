import speech_recognition as sr
import time

from gtts import gTTS
import os
import time
import pygame

def hablar(texto, idioma='es', nombre_archivo="temp_audio.mp3", velocidad_normal=True):
    """
    Convierte texto a voz usando gTTS y lo reproduce al instante con pygame.

    Args:
        texto (str): El texto que se va a convertir a voz.
        idioma (str): El código del idioma (ej. 'es' para español, 'es-es' para español de España).
        nombre_archivo (str): Nombre temporal del archivo MP3 a guardar y reproducir.
        velocidad_normal (bool): Si es True, la velocidad es normal. Si es False, es más lenta.
    """
    try:
        # Crea el objeto gTTS
        tts = gTTS(text=texto, lang=idioma, slow=not velocidad_normal)

        # Guarda el archivo de audio temporal
        tts.save(nombre_archivo)
        print(f"Audio generado y guardado como '{nombre_archivo}'")

        # Inicializa el mezclador de pygame
        # Frecuencia de muestreo (Hz), Tamaño del buffer de audio, Canales (1=mono, 2=estéreo), Tamaño del buffer
        # A menudo 44100 Hz es bueno para MP3.
        pygame.mixer.init(44100, -16, 2, 2048) # Puedes ajustar estos valores si tienes problemas de audio
        
        # Carga el archivo de audio
        pygame.mixer.music.load(nombre_archivo)
        
        # Reproduce el audio
        pygame.mixer.music.play()
        print("Reproduciendo audio con Pygame...")

        # Espera a que la reproducción termine
        while pygame.mixer.music.get_busy():
            time.sleep(0.1) # Pequeña pausa para no consumir CPU innecesariamente

    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Asegúrate de haber instalado 'pygame' y 'gTTS' correctamente.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        print("Asegúrate de tener conexión a internet para gTTS y las dependencias de audio de Pygame instaladas.")
    finally:
        # Detiene el mezclador de Pygame y lo quita del sistema
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        # Intenta eliminar el archivo temporal después de la reproducción
        if os.path.exists(nombre_archivo):
            os.remove(nombre_archivo)
            print(f"Archivo temporal '{nombre_archivo}' eliminado.")

def escuchar_y_detectar_comando_continuo(frase_a_reproducir):
    hablar(frase_a_reproducir)
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando continuamente...")
        r.adjust_for_ambient_noise(source)

        while True:
            print("Di algo (o espera un momento de silencio para procesar)...")
            try:
                # Escucha durante un periodo más largo (ej. 10 segundos o hasta que haya un silencio significativo)
                audio = r.listen(source, phrase_time_limit=15) # Ajusta según necesidad

                print("Procesando audio...")
                texto = r.recognize_google(audio, language="es-ES")
                print(f"Google Speech Recognition dice: {texto}")

                # Lista de palabras clave que queremos detectar
                palabras_clave = [
                    "arriba", "abajo", "izquierda", "derecha",
                    "uno", "dos", "tres", "cuatro", "cinco", "seis",
                    "1", "2", "3", "4", "5", "6"
                ]

                # Convertir el texto reconocido a minúsculas para una comparación sin distinción entre mayúsculas y minúsculas
                texto_lower = texto.lower()

                # Iterar sobre las palabras clave para ver si alguna está en el texto
                for palabra in palabras_clave:
                    if palabra in texto_lower:
                        # Si se encuentra una palabra clave, devolverla y salir de la función
                        print(f"Comando detectado: {palabra}")
                        return palabra, texto  # Devolvemos la palabra detectada y el texto completo


            except sr.WaitTimeoutError:
                print("No se detectó voz en el tiempo de espera.")
                continue
            except sr.UnknownValueError:
                print("Google Speech Recognition no pudo entender el audio.")
            except sr.RequestError as e:
                print(f"Error con la solicitud a Google Speech Recognition; {0}".format(e))
                time.sleep(5) # Esperar un poco antes de reintentar
                continue
            except Exception as e:
                print(f"Ocurrió un error inesperado: {e}")
                time.sleep(5)
                continue