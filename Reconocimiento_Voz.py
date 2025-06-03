import speech_recognition as sr
import time

def escuchar_y_detectar_comando_continuo():
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

                if "pon la ficha" in texto.lower():
                    # Aquí puedes añadir la lógica para "poner la ficha 3"
                    # Si solo necesitas detectarlo una vez, puedes usar 'break' aquí
                    return 1, texto
                if "confirmar ficha" in texto.lower():
                    # Aquí puedes añadir la lógica para "quitar la ficha 3"
                    # Si solo necesitas detectarlo una vez, puedes usar 'break' aquí
                    return 2, texto
                if "cambiar ficha" in texto.lower():
                    # Aquí puedes añadir la lógica para "cambiar la ficha 3"
                    # Si solo necesitas detectarlo una vez, puedes usar 'break' aquí
                    return 3, texto
                if "siguiente posicion" in texto.lower():
                    # Aquí puedes añadir la lógica para "siguiente posición"
                    # Si solo necesitas detectarlo una vez, puedes usar 'break' aquí
                    return 4, texto
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