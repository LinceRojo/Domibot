from Detectar_Domino import obtener_estado, Obtener_Ficha_Imagen, obtener_puntuacion_ficha, obtener_fichas_jugador
from Reconocimiento_Voz import escuchar_y_detectar_comando_continuo
import cv2
import numpy as np
from Domibot import DominoRobotController, pixel_to_world_linear
import time

# for ficha in fichas:
    #     print(f"Ficha {ficha.indice}:")
    #     print(f"  Coordenadas: {ficha.coordenadas}")
    #     print(f"  Vecino: {ficha.posicion_vecino if ficha.posicion_vecino else 'ninguno'}")
    #     print(f"  Número de vecinos: {ficha.num_vecinos}")

def obtener_estado_completo(img_path_tablero, img_path_jugador):
    """
    Función para obtener el estado completo del juego de dominó.
    """
    fichas_borde_data = obtener_estado(img_path_tablero)

    posibles_fichas = []

    print("Fichas en bordes detectadas:")
    for i, ficha_data in enumerate(fichas_borde_data):
        print(f"Ficha {i}:")
        print(f"  Coordenadas: {ficha_data[0]}")
        print(f"  Vecino: {ficha_data[1]}")
        print(f"  Número de vecinos: {ficha_data[2]}")

        img = Obtener_Ficha_Imagen(img_path_tablero, ficha_data[0])

        puntuacion = obtener_puntuacion_ficha(ficha_data[0], ficha_data[1],img_path_tablero, True)
        print(f"  Puntuación: {puntuacion}")
        # Añadir la puntuación a la lista de datos de la ficha
        fichas_borde_data[i].append(puntuacion)
        posibles_fichas.append(puntuacion)

    fichas_jugador_data = obtener_fichas_jugador(img_path_jugador)

    print("Fichas del jugador disponibles:")
    for i, ficha_data in enumerate(fichas_jugador_data):
        print(f"Ficha {i}:")
        print(f"  Coordenadas: {ficha_data[0]}")
        puntuacion = obtener_puntuacion_ficha(ficha_data[0], ficha_data[1],img_path_jugador, True)
        print(f"  Puntuación: {puntuacion[0]}, {puntuacion[1]}")
        # Añadir la puntuación a la lista de datos de la ficha
        fichas_jugador_data[i].append(puntuacion)

        img = Obtener_Ficha_Imagen(img_path_jugador, ficha_data[0])

    return fichas_borde_data, fichas_jugador_data, posibles_fichas

def bbox_center(bbox):
    """
    Calcula el centro (u, v) en píxeles del bounding box.
    
    Parámetros:
        bbox (dict): Diccionario con keys 'x1', 'y1', 'x2', 'y2'
    
    Retorna:
        (u, v): Coordenadas del centro del bounding box en píxeles
    """
    x1, y1 = bbox['x1'], bbox['y1']
    x2, y2 = bbox['x2'], bbox['y2']

    u_center = (x1 + x2) / 2
    v_center = (y1 + y2) / 2

    return u_center, v_center



# ------------ USO DEL ROBOT DOMINO -------------------

robot_controller = DominoRobotController(port=19999)

if robot_controller.clientID != -1:
    # Movemos a posición inicial
    robot_controller.move_posicion_inicial()
    time.sleep(2)
    
    # Obtener foto
    image = robot_controller.obtener_foto()
    
    # Separamos la imagen por la mitad (parte de arriba y de abajo) y lo guardamos en dos archivos
    if image is not None:
        # La imagen debe ser rgb
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, _ = image.shape
        # La parte de arriba debe ser dos tercios de la imagen
        top_two_thirds = image[:2*height//3, :]
        bottom_one_third = image[2*height//3:, :]
        cv2.imwrite("parte_superior.png", top_two_thirds)
        cv2.imwrite("parte_inferior.png", bottom_one_third)
    
    robot_controller.move_posicion_recta()
    time.sleep(2)
    # Obtenemos coordenada
    fichas_borde_data, fichas_jugador_data, posibles_fichas = obtener_estado_completo("parte_superior.png", "parte_inferior.png")

    for i, ficha_data in enumerate(fichas_jugador_data):
        center_x, center_y = bbox_center(ficha_data[0])
        print(f"Ficha {i} del jugador: Coordenadas del centro (u, v): ({center_x}, {center_y})")
        real_x, real_y = pixel_to_world_linear(center_x, center_y)
        print(f"Ficha {i} del jugador: Coordenadas reales (x, y): ({real_x}, {real_y})")

        # Ejemplo cinemática inversa para mover efector final
        if i == 0:
            robot_controller.move_domino(px=real_x, py=real_y, roll=0, yaw=90)
            time.sleep(2)
            robot_controller.coger_ficha()
            time.sleep(2)
    
    time.sleep(3)

    # Mover a posición de juego
    robot_controller.move_posicion_recta()
    time.sleep(2)

    # Soltar ficha
    robot_controller.soltar_ficha()
    time.sleep(2)

    #robot_controller.move_joint_by_delta('joint3', -5)

    time.sleep(2)
    
    robot_controller.disconnect()
else:
    print("No se pudo inicializar el controlador del robot.")

# accion, texto = escuchar_y_detectar_comando_continuo()

# for posible_ficha in posibles_fichas:
#     if posible_ficha in texto.lower():
#         print(f"El jugador ha decidido jugar la ficha con puntuación {decision_jugador}.")
#     else:
#         print(f"El jugador ha seleccionado una ficha incorrecta. Las puntuaciones posibles son: {posibles_fichas}")
#     print(f"Texto reconocido: {texto}")
#     print(f"Posible ficha: {posible_ficha}")
