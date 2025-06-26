from Virtual_Controllers.Detectar_Domino import es_horizontal_o_vertical

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
        print(f"Tipo de ficha: {type(ficha_data[3])}, Comparar con: {int}")
        if type(ficha_data[3]) == int:
            valor_ficha = ficha_data[3]
        else:
            valor_ficha = ficha_data[3][0]
        print(f"Valor de la ficha en el borde: {valor_ficha}")
        if valor_ficha == int(valor_ficha_jugador):
            print(f"Valor de la ficha del jugador {valor_ficha_jugador} coincide con la ficha en el borde {ficha_data[3]}")
            fichas_posibles.append(ficha_data)
    
    return fichas_posibles

def calcular_coordenada_juego(ficha_posible, ANCHURA_FICHA=40, LONGITUD_FICHA=80):
    """
    Calcula las coordenadas relativas a la ficha donde se puede jugar y devuelve un diccionario con las orientaciones y coordenadas.
    Args:
        ficha_posible (dict): Diccionario con las coordenadas de la ficha posible.
    Returns:
        posibles_coordenadas (dict): Diccionario con las coordenadas relativas a la ficha donde se puede jugar.
    """
    posibles_coordenadas = {}
    # Decidimos que direcciones posibles son:
    
    print(f"Ficha posible: {ficha_posible}")

    if type(ficha_posible[3]) == list and len(ficha_posible[3]) == 2:
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

    for direccion in direcciones:
        orientacion = calcular_nueva_orientacion(ficha_posible, direccion)
        print(f"Coordenada antes de calcular: {ficha_posible[0]}")
        posibles_coordenadas[direccion] = calcular_coordenada_relativa(direccion, orientacion, ficha_posible, ANCHURA_FICHA=ANCHURA_FICHA, LONGITUD_FICHA=LONGITUD_FICHA)
        print(f"Coordenada calculada para {direccion}: {posibles_coordenadas[direccion]}")
    
    return posibles_coordenadas

def calcular_nueva_orientacion(ficha_origen, direccion):
    """
    Calcula la nueva orientación de acuerdo a la ficha origen, si la ficha no es de la misma puntuacion en ambas partes,
    la nueva ficha tendrá la misma orientación que la ficha origen.
    Si la ficha origen es una ficha doble, la nueva orientación será la opuesta.
    """
    print(f"Calculando nueva orientación para ficha origen: {ficha_origen} y dirección: {direccion}")
    print(f"Puntuación de la ficha origen: {ficha_origen[3]}")
    orientacion = es_horizontal_o_vertical(ficha_origen[0])
    print(f"Orientación de la ficha origen: {orientacion}")
    if type(ficha_origen[3]) == list and len(ficha_origen[3]) == 2:
        print(f"La ficha origen es doble: {ficha_origen[3]}")
        # Si la ficha es doble, la nueva orientación será la opuesta si la direccion es en el sentido de la orientacion
        if direccion in ["izquierda", "derecha"]:
            if orientacion == "horizontal":
                return "vertical"
            else:
                return "horizontal"
        elif direccion in ["arriba", "abajo"]:
            if orientacion == "vertical":
                return "vertical"
            else:
                return "horizontal"
    else:
        # Si no es doble, mantenemos la misma orientación
        return orientacion


def calcular_coordenada_relativa(direccion, orientacion, ficha_origen, ANCHURA_FICHA = 40 ,LONGITUD_FICHA = 80):
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
    orientacion_origen = es_horizontal_o_vertical(ficha_origen[0])

    x_origen, y_origen = bbox_center(ficha_origen[0])

    offset_origen_x, offset_origen_y = calcular_offset(orientacion_origen, direccion, LONGITUD_FICHA, ANCHURA_FICHA)
    offset_nuevo_x, offset_nuevo_y = calcular_offset(orientacion, direccion, LONGITUD_FICHA, ANCHURA_FICHA)

    print(f"Dirección: {direccion}")
    print(f"Orientación origen: {orientacion_origen}")
    print(f"Orientación nueva: {orientacion}")
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
            return (0, -anchura_ficha / 2)
        elif direccion == "abajo":
            return (0, anchura_ficha / 2)
    else:  # vertical
        if direccion == "izquierda":
            return (-anchura_ficha / 2, 0)
        elif direccion == "derecha":
            return (anchura_ficha / 2, 0)
        elif direccion == "arriba":
            return (0, -longitud_ficha / 2)
        elif direccion == "abajo":
            return (0, longitud_ficha / 2)

    return (0, 0)  # Por defecto no debería llegar aquí

def calcular_rotacion(puntuacion_ficha_jugador, direccion, puntuacion_elegida):
    """
    Calcula la rotación necesaria para colocar la ficha en la dirección correcta.
    Si la puntuación elegida esta en la primera posición de la ficha, la puntuación está arriba,
    si está en la segunda posición, la puntuación está abajo.
    """
    diccionario_rotacion = {
        "izquierda": -90,
        "derecha": 90,
        "arriba": 180,
        "abajo": 0
    }

    print(f"Calculando rotación para la puntuación {puntuacion_ficha_jugador} en dirección {direccion} con puntuación elegida {puntuacion_elegida}")

    if type(puntuacion_ficha_jugador) == list and len(puntuacion_ficha_jugador) == 2:
        if int(puntuacion_elegida) == puntuacion_ficha_jugador[0]:
            print(f"La puntuación elegida {puntuacion_elegida} es la primera de la ficha {puntuacion_ficha_jugador}.")
            return diccionario_rotacion[direccion]
        else:
            print(f"La puntuación elegida {puntuacion_elegida} es la segunda de la ficha {puntuacion_ficha_jugador}.")
            return (diccionario_rotacion[direccion] + 180) % 360
