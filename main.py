from Detectar_Domino import obtener_estado, Obtener_Ficha_Imagen, obtener_puntuacion_ficha
import cv2
import numpy as np

# for ficha in fichas:
    #     print(f"Ficha {ficha.indice}:")
    #     print(f"  Coordenadas: {ficha.coordenadas}")
    #     print(f"  Vecino: {ficha.posicion_vecino if ficha.posicion_vecino else 'ninguno'}")
    #     print(f"  Número de vecinos: {ficha.num_vecinos}")

fichas_borde_data = obtener_estado("Ejemplo-Domino.jpg")

decision_jugador = 3

posibles_fichas = []

print("Fichas en bordes detectadas:")
for i, ficha_data in enumerate(fichas_borde_data):
    print(f"Ficha {i}:")
    print(f"  Coordenadas: {ficha_data[0]}")
    print(f"  Vecino: {ficha_data[1]}")
    print(f"  Número de vecinos: {ficha_data[2]}")

    img = Obtener_Ficha_Imagen("Ejemplo-Domino.jpg", ficha_data[0])
    cv2.imshow("Recorte", img)
    cv2.waitKey(0)

    puntuacion = obtener_puntuacion_ficha(ficha_data[0], ficha_data[1],"Ejemplo-Domino.jpg", True)
    print(f"  Puntuación: {puntuacion}")
    # Añadir la puntuación a la lista de datos de la ficha
    fichas_borde_data[i].append(puntuacion)
    posibles_fichas.append(puntuacion)

if decision_jugador in posibles_fichas:
    print(f"El jugador ha decidido jugar la ficha con puntuación {decision_jugador}.")
else:
    print(f"El jugador ha seleccionado una ficha incorrecta. Las puntuaciones posibles son: {posibles_fichas}")
    