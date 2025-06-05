from Detectar_Domino import obtener_estado, Obtener_Ficha_Imagen, obtener_puntuacion_ficha, obtener_fichas_jugador
from Reconocimiento_Voz import escuchar_y_detectar_comando_continuo
import cv2
import numpy as np
from Domibot import DominoRobotController, pixel_to_world_linear
import time

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

def ordenar_fichas_jugador_por_coordenadas(fichas_jugador_data):
    """
    Ordena una lista de fichas de jugador de izquierda a derecha
    basándose en la coordenada X de sus bounding boxes.

    Args:
        fichas_jugador_data (list): Una lista de tuplas, donde cada tupla representa una ficha
                                    y contiene (bbox_dict, puntuacion_tuple).
                                    Ej: ({'x1': 10, 'y1': 20, 'x2': 50, 'y2': 60}, (1, 2))

    Returns:
        list: La lista de fichas de jugador ordenada de izquierda a derecha.
    """
    # Creamos una lista temporal para almacenar el centro X junto con los datos de la ficha
    fichas_con_centro_x = []
    for ficha_data in fichas_jugador_data:
        # ficha_data[0] es el diccionario de coordenadas (bbox_dict)
        center_x, _ = bbox_center(ficha_data[0])
        fichas_con_centro_x.append((center_x, ficha_data))

    # Ordenamos la lista basándonos en la coordenada X del centro
    fichas_ordenadas = sorted(fichas_con_centro_x, key=lambda item: item[0])

    # Devolvemos solo los datos originales de la ficha, ya ordenados
    return [item[1] for item in fichas_ordenadas]

def obtener_valores_comunes_y_coincidencia(puntuacion_ficha_jugador, posibles_fichas_en_tablero):
    """
    Verifica si alguno de los valores en la puntuación de una ficha de jugador
    coincide con alguno de los valores en la lista de posibles fichas del tablero.

    Args:
        puntuacion_ficha_jugador (tuple or list): Una tupla o lista de dos números
                                                   que representa la puntuación de la ficha del jugador (ej. (5, 3)).
        posibles_fichas_en_tablero (list): Una lista de números enteros que representan
                                           los valores de los extremos del dominó en el tablero donde se puede conectar.

    Returns:
        tuple: Una tupla que contiene:
               - bool: True si hay al menos un valor en común, False en caso contrario.
               - list: Una lista de los valores comunes encontrados.
    """
    valores_comunes = []
    
    # Iteramos sobre cada valor de la ficha del jugador
    for valor_jugador in puntuacion_ficha_jugador:
        # Verificamos si este valor del jugador está en la lista de posibles fichas del tablero
        if valor_jugador in posibles_fichas_en_tablero:
            valores_comunes.append(valor_jugador)
            
    # Si la lista de valores_comunes no está vacía, significa que hubo al menos una coincidencia
    hay_coincidencia = len(valores_comunes) > 0
    
    return hay_coincidencia, valores_comunes

def obtener_fichas_posibles_donde_jugar(fichas_borde_data, valor_ficha_jugador):
    """
    Obtiene las posiciones posibles donde se puede jugar una ficha del jugador
    basándose en los valores de las fichas en los bordes del tablero.

    Args:
        fichas_borde_data (list): Lista de datos de las fichas en los bordes del tablero.
                                  Cada elemento es una tupla con coordenadas y puntuación.
        valor_ficha_jugador (int): Valor de la ficha del jugador que se quiere jugar.

    Returns:
        list: Lista de fichas posibles donde se puede jugar la ficha del jugador.
    """
    fichas_posibles = []
    
    for ficha_data in fichas_borde_data:
        print(f"Procesando ficha en el borde: {ficha_data[0]} con vecino {ficha_data[1]} y puntuación {ficha_data[3]}")
        # Comprobamos si el valor de la ficha del jugador coincide con la puntuación de la ficha en el borde
        print(f"Comprobando ficha: {ficha_data[3]} contra valor del jugador: {valor_ficha_jugador}")
        if ficha_data[3] == int(valor_ficha_jugador):
            print(f"Valor de la ficha del jugador {valor_ficha_jugador} coincide con la ficha en el borde {ficha_data[3]}")
            fichas_posibles.append(ficha_data)
    
    return fichas_posibles

def calcular_coordenada_juego(ficha_posible):
    """
    Calcula las coordenadas relativas a la ficha donde se puede jugar y devuelve un diccionario con las orientaciones y coordenadas.
    Args:
        ficha_posible (dict): Diccionario con las coordenadas de la ficha posible.
    Returns:
        posibles_coordenadas (dict): Diccionario con las coordenadas relativas a la ficha donde se puede jugar.
    """
    posibles_coordenadas = {}
    # Decidimos que direcciones posibles son:
    
    if type(ficha_posible[2]) == list and len(ficha_posible[2]) == 2:
        # Si la ficha tiene dos valores, es una ficha doble, por tanto, puede jugarse en cualquier orientación excepto la del vecino
        direcciones = ["izquierda", "derecha", "arriba", "abajo"]
        direcciones.remove(ficha_posible[1])  # Eliminamos la dirección del vecino
    else:
        if ficha_posible[1] == "izquierda":
            direcciones = ["derecha"]
        elif ficha_posible[1] == "derecha":
            direcciones = ["izquierda"]
        elif ficha_posible[1] == "arriba":
            direcciones = ["abajo"]
        elif ficha_posible[1] == "abajo":
            direcciones = ["arriba"]

    orientacion = es_horizontal_o_vertical(ficha_posible)
    for direccion in direcciones:
        print(f"Coordenada antes de calcular: {ficha_posible[0]}")
        posibles_coordenadas[direccion] = calcular_coordenada_relativa(direccion, orientacion, ficha_posible)
        print(f"Coordenada calculada para {direccion}: {posibles_coordenadas[direccion]}")
    
    return posibles_coordenadas

def es_horizontal_o_vertical(ficha):
    """
    Determina si la ficha es horizontal o vertical basándose en sus coordenadas.

    Args:
        ficha (FichaDomino): Objeto que contiene informacion de la ficha.

    Returns:
        str: "horizontal" si la ficha es horizontal, "vertical" si es vertical.
    """
    x1, y1 = ficha[0]['x1'], ficha[0]['y1']
    x2, y2 = ficha[0]['x2'], ficha[0]['y2']
    
    if abs(x2 - x1) > abs(y2 - y1):
        return "horizontal"
    else:
        return "vertical"
    
def calcular_coordenada_relativa(direccion, orientacion, ficha_origen):
    """
    Calcula las coordenadas donde se puede jugar una ficha en función de la dirección y la orientación.

    Args:
        direccion (str): Dirección donde se quiere jugar la ficha ("izquierda", "derecha", "arriba", "abajo").
        orientacion (str): Orientación de la ficha ("horizontal" o "vertical").
        ficha_origen (dict): Diccionario con las coordenadas del centro de la ficha origen,
                             con claves 'u' y 'v'.

    Returns:
        tuple: Coordenadas (u, v) del centro donde se puede jugar la ficha.
    """
    # Tamaño aproximado de la ficha
    orientacion_origen = es_horizontal_o_vertical(ficha_origen)
    
    ANCHURA_FICHA = 40
    LONGITUD_FICHA = 80

    x_origen, y_origen = bbox_center(ficha_origen[0])

    offset_origen_x, offset_origen_y = calcular_offset(orientacion_origen, direccion, LONGITUD_FICHA, ANCHURA_FICHA)
    offset_nuevo_x, offset_nuevo_y = calcular_offset(orientacion, direccion, LONGITUD_FICHA, ANCHURA_FICHA)

    print(f"Offset origen: ({offset_origen_x}, {offset_origen_y})")
    print(f"Offset nuevo: ({offset_nuevo_x}, {offset_nuevo_y})")

    x_nueva = x_origen + offset_origen_x + offset_nuevo_x
    y_nueva = y_origen + offset_origen_y + offset_nuevo_y

    return (x_nueva, y_nueva)

def calcular_offset(orientacion, direccion, longitud_ficha, anchura_ficha):
    """
    Calcula el offset en función de la orientación y dirección.

    Args:
        orientacion (str): Orientación de la ficha ("horizontal" o "vertical").
        direccion (str): Dirección donde se quiere jugar la ficha ("izquierda", "derecha", "arriba", "abajo").
        longitud_ficha (int): Longitud de la ficha.
        anchura_ficha (int): Anchura de la ficha.

    Returns:
        tuple: Offset en x e y.
    """
    if orientacion == "horizontal":
        if direccion == "izquierda":
            return (-longitud_ficha / 2, 0)
        elif direccion == "derecha":
            return (longitud_ficha / 2, 0)
        elif direccion == "arriba":
            return (0, anchura_ficha / 2)
        elif direccion == "abajo":
            return (0, -anchura_ficha / 2)
    else:  # vertical
        if direccion == "izquierda":
            return (-anchura_ficha / 2, 0)
        elif direccion == "derecha":
            return (anchura_ficha / 2, 0)
        elif direccion == "arriba":
            return (0, longitud_ficha / 2)
        elif direccion == "abajo":
            return (0, -longitud_ficha / 2)

    return (0, 0)  # Por defecto no debería llegar aquí


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
        cv2.imwrite("imagen_tablero.png", image)
        height, width, _ = image.shape
        # La parte de arriba debe ser dos tercios de la imagen
        top_two_thirds = image[:2*height//3, :]
        bottom_one_third = image[2*height//3:, :]
        cv2.imwrite("parte_superior.png", top_two_thirds)
        cv2.imwrite("parte_inferior.png", bottom_one_third)
        print("Size parte superior:", top_two_thirds.shape)
        print("Size parte inferior:", bottom_one_third.shape)
    
    robot_controller.move_posicion_recta()
    time.sleep(2)
    # Obtenemos coordenada
    fichas_borde_data, fichas_jugador_data, posibles_fichas = obtener_estado_completo("parte_superior.png", "parte_inferior.png")
    fichas_jugador_data = ordenar_fichas_jugador_por_coordenadas(fichas_jugador_data)
    print("Fichas del jugador ordenadas de izquierda a derecha:")   
    for i, ficha_data in enumerate(fichas_jugador_data):
        print(f"Ficha {i}: Coordenadas: {ficha_data[0]}, Puntuación: {ficha_data[3]}")
    
    ficha_correcta = False
    while ficha_correcta == False:
        # Preguntar al jugador qué ficha quiere jugar, con una entrada de texto
        numero_ficha = input("¿Qué ficha quieres jugar? (Introduce el número de la ficha): ")
        numero_ficha = int(numero_ficha) if numero_ficha.isdigit() else None

        # Validar que el número de ficha es válido
        hay_coincidencia, puntuaciones_posibles = obtener_valores_comunes_y_coincidencia(fichas_jugador_data[numero_ficha][3], posibles_fichas)
        if hay_coincidencia:
            ficha_correcta = True
            print(f"El jugador ha decidido jugar la ficha con puntuación {numero_ficha}.")
            center_x, center_y = bbox_center(fichas_jugador_data[numero_ficha][0])
            print(f"Ficha {i} del jugador: Coordenadas del centro (u, v): ({center_x}, {center_y+320})")
            real_x, real_y = pixel_to_world_linear(center_x, center_y+320)
            print(f"Ficha {i} del jugador: Coordenadas reales (x, y): ({real_x}, {real_y})")

            robot_controller.move_domino(px=real_x, py=real_y, roll=0, yaw=90)
            time.sleep(2)
            robot_controller.coger_ficha()
            time.sleep(2)

            if len(puntuaciones_posibles) > 1:
                puntuacion_valida = False
                while not puntuacion_valida:
                    print(f"El jugador ha seleccionado una ficha con múltiples puntuaciones posibles: {puntuaciones_posibles}.")
                    # Pedimos al jugador que confirme el valor de la ficha
                    decision_jugador = input(f"¿Cuál es el valor de la ficha que quieres jugar? (Posibles valores: {puntuaciones_posibles}): ")
                    
                    if decision_jugador.isdigit() and int(decision_jugador) in puntuaciones_posibles:
                        print(f"El jugador ha confirmado que la ficha tiene el valor {decision_jugador}.")
                        puntuacion_valida = True
                    else:
                        print(f"El jugador ha seleccionado un valor incorrecto. Las puntuaciones posibles son: {puntuaciones_posibles}")
                        puntuacion_valida = False
            else:
                decision_jugador = puntuaciones_posibles[0]
            
            # Mover a posición de juego
            fichas_posibles = obtener_fichas_posibles_donde_jugar(fichas_borde_data, decision_jugador)
            if fichas_posibles:
                if len(fichas_posibles) > 1:
                    confirmar_posicion = True
                else:
                    confirmar_posicion = False

                print(f"Posibles posiciones para jugar la ficha {decision_jugador}: {fichas_posibles}")
                robot_controller.move_posicion_recta()
                time.sleep(2)

                # coordenadas_posicion = bbox_center(fichas_posibles[0][0])
                # real_x_posicion, real_y_posicion = pixel_to_world_linear(coordenadas_posicion[0], coordenadas_posicion[1]+160)
                # robot_controller.move_domino(px=real_x_posicion, py=real_y_posicion, roll=0, yaw=90)
                time.sleep(2)

                # Extra step de confirmar la posición (TODO)

                # Solicitar al jugador posición relativa a la ficha y orientación
                coordenada_calculada = calcular_coordenada_juego(fichas_posibles[0])

                # Elegir direccion si hay más de una
                if len(coordenada_calculada) > 1:
                    print(f"Hay varias posiciones posibles para jugar la ficha {decision_jugador}.")
                    print(f"Posiciones posibles: {coordenada_calculada}")
                    # Pedir al jugador que elija una posición
                    direccion = input("¿En qué dirección quieres jugar la ficha? (izquierda, derecha, arriba, abajo): ")
                    if direccion in coordenada_calculada:
                        coordenada_calculada = coordenada_calculada[direccion]
                    else:
                        print(f"Dirección {direccion} no válida. Usando la primera posición disponible.")
                        coordenada_calculada = list(coordenada_calculada.values())[0]
                else:
                    coordenada_calculada = list(coordenada_calculada.values())[0]

                real_x_posicion, real_y_posicion = pixel_to_world_linear(coordenada_calculada[0], coordenada_calculada[1])
                print(f"Coordenadas calculadas para jugar la ficha: {coordenada_calculada[0], coordenada_calculada[1]}")
                print(f"Coordenadas reales para jugar la ficha: ({real_x_posicion}, {real_y_posicion})")
                robot_controller.move_domino(px=real_x_posicion, py=real_y_posicion, roll=0, yaw=0, rotacion=90)
                time.sleep(2)
                # Soltar ficha
                robot_controller.soltar_ficha()
                print("Ficha soltada en la posición correcta.")
                time.sleep(2)
            else:
                print(f"No hay posiciones disponibles para jugar la ficha {decision_jugador}.")

        else:
            print(f"El jugador ha seleccionado una ficha incorrecta. Las puntuaciones posibles son: {posibles_fichas}")


    # for i, ficha_data in enumerate(fichas_jugador_data):
    #     center_x, center_y = bbox_center(ficha_data[0])
    #     print(f"Ficha {i} del jugador: Coordenadas del centro (u, v): ({center_x}, {center_y})")
    #     real_x, real_y = pixel_to_world_linear(center_x, center_y)
    #     print(f"Ficha {i} del jugador: Coordenadas reales (x, y): ({real_x}, {real_y})")

    #     # Ejemplo cinemática inversa para mover efector final
    #     if i == 0:
    #         robot_controller.move_domino(px=real_x, py=real_y, roll=0, yaw=90)
    #         time.sleep(2)
    #         robot_controller.coger_ficha()
    #         time.sleep(2)
    
    time.sleep(3)

    # Mover a posición de juego
    robot_controller.move_posicion_recta()

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
