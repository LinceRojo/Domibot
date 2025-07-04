import cv2
import numpy as np
import os


class FichaDomino:
    def __init__(self, indice, x, y, w, h, num_vecinos=0, puntuacion=-1, posicion_vecino=None, vecino_idx=None):
        self.indice = indice
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.posicion_vecino = posicion_vecino  # "arriba", "abajo", "izquierda", "derecha"
        self.vecino_idx = vecino_idx
        self.num_vecinos = num_vecinos
        self.puntuacion = puntuacion
        
    @property
    def coordenadas(self):
        """Devuelve las coordenadas de los bordes de la ficha"""
        return {
            'x1': self.x,
            'y1': self.y,
            'x2': self.x + self.width,
            'y2': self.y + self.height
        }
    
    @property
    def datos(self):
        """Devuelve los datos principales en formato de array"""
        return [
            self.coordenadas,
            self.posicion_vecino if self.posicion_vecino else "ninguno",
            self.num_vecinos
        ]
    
    def recortar_ficha(self, imagen):
        """Recorta la ficha de la imagen original"""
        return imagen[self.y:self.y+self.height, self.x:self.x+self.width]
    
    def dibujar_indicador_vecino(self, imagen_ficha):
        """Dibuja el indicador de la posición del vecino en la imagen de la ficha"""
        if not self.posicion_vecino:
            return imagen_ficha
        
        h, w = imagen_ficha.shape[:2]
        color = (0, 255, 255)  # Amarillo
        grosor = 3
        
        if self.posicion_vecino == "izquierda":
            cv2.line(imagen_ficha, (5, h//2), (w//4, h//2), color, grosor)
            cv2.circle(imagen_ficha, (5, h//2), 5, color, -1)
        elif self.posicion_vecino == "derecha":
            cv2.line(imagen_ficha, (w-5, h//2), (3*w//4, h//2), color, grosor)
            cv2.circle(imagen_ficha, (w-5, h//2), 5, color, -1)
        elif self.posicion_vecino == "arriba":
            cv2.line(imagen_ficha, (w//2, 5), (w//2, h//4), color, grosor)
            cv2.circle(imagen_ficha, (w//2, 5), 5, color, -1)
        elif self.posicion_vecino == "abajo":
            cv2.line(imagen_ficha, (w//2, h-5), (w//2, 3*h//4), color, grosor)
            cv2.circle(imagen_ficha, (w//2, h-5), 5, color, -1)
        
        return imagen_ficha

class DetectorDominoes:
    def __init__(self, umbral_distancia=15):
        self.umbral_distancia = umbral_distancia
    
    def procesar_imagen(self, original_path, bw_output_path, simulacion=True):
        """Convierte la imagen original a blanco y negro para procesamiento"""
        img = cv2.imread(original_path)
        if img is None:
            raise FileNotFoundError(f"No se pudo leer la imagen en {original_path}")
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if simulacion:
            lower_white = np.array([0, 0, 210])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
        else:
            lower_white = np.array([0, 0, 200])   # Bajamos un poco el brillo mínimo para capturar blancos más oscuros
            upper_white = np.array([179, 50, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
        cv2.imwrite(bw_output_path, white_mask)
        print(f"Guardando imagen")
        return white_mask
    
    def detectar_fichas(self, mascara_path, tamaño_aprox, original_path, output_dir="./Media_Stream/fichas_borde", simulacion= True):
        """Detecta fichas de dominó en la imagen y devuelve objetos FichaDomino"""
        mascara = cv2.imread(mascara_path, cv2.IMREAD_GRAYSCALE)
        original_img = cv2.imread(original_path)
        
        if mascara is None:
            raise FileNotFoundError(f"No se pudo leer la máscara en {mascara_path}")
        if original_img is None:
            raise FileNotFoundError(f"No se pudo leer la imagen original en {original_path}")
        
        _, binary = cv2.threshold(mascara, 127, 255, cv2.THRESH_BINARY)
        contornos, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar contornos por tamaño
        contornos_filtrados = [
            cnt for cnt in contornos 
            if tamaño_aprox * 0.5 < cv2.contourArea(cnt) < tamaño_aprox * 1.5
        ]
        
        # Crear objetos FichaDomino
        fichas = []
        for idx, cnt in enumerate(contornos_filtrados):
            x, y, w, h = cv2.boundingRect(cnt)
            fichas.append(FichaDomino(idx, x, y, w, h))
        
        # Determinar adyacencias y vecinos
        self._determinar_vecinos(fichas)
        
        # Procesar fichas de borde
        fichas_borde = [f for f in fichas if f.posicion_vecino is not None]
        self._guardar_fichas_borde(fichas_borde, original_img, output_dir)
        
        return fichas
    
    def _determinar_vecinos(self, fichas):
        """Determina qué fichas son vecinas y en qué posición"""
        for i, ficha in enumerate(fichas):
            vecinos = []
            for j, otra_ficha in enumerate(fichas):
                if i != j:
                    direccion = self._son_adyacentes(
                        (ficha.x, ficha.y, ficha.width, ficha.height),
                        (otra_ficha.x, otra_ficha.y, otra_ficha.width, otra_ficha.height)
                    )
                    if direccion:
                        vecinos.append((j, direccion))
            
            # Guardamos cantidad de vecinos
            ficha.num_vecinos = len(vecinos)

            # Si solo tiene un vecino, está en un borde
            if len(vecinos) == 1:
                vecino_idx, direccion = vecinos[0]
                ficha.posicion_vecino = self._determinar_posicion_relativa(
                    (ficha.x, ficha.y, ficha.width, ficha.height),
                    (fichas[vecino_idx].x, fichas[vecino_idx].y, 
                     fichas[vecino_idx].width, fichas[vecino_idx].height),
                    direccion
                )
                ficha.vecino_idx = vecino_idx
    
    def _son_adyacentes(self, rect1, rect2):
        """Determina si dos rectángulos son adyacentes y en qué dirección"""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        left1, right1 = x1, x1 + w1
        top1, bottom1 = y1, y1 + h1
        left2, right2 = x2, x2 + w2
        top2, bottom2 = y2, y2 + h2
        
        superposicion_x = (left1 <= right2 + self.umbral_distancia) and (right1 >= left2 - self.umbral_distancia)
        superposicion_y = (top1 <= bottom2 + self.umbral_distancia) and (bottom1 >= top2 - self.umbral_distancia)
        
        # Adyacencia horizontal (misma altura)
        if superposicion_y and (abs(left1 - right2) <= self.umbral_distancia or abs(left2 - right1) <= self.umbral_distancia):
            return "horizontal"
        # Adyacencia vertical (misma anchura)
        if superposicion_x and (abs(top1 - bottom2) <= self.umbral_distancia or abs(top2 - bottom1) <= self.umbral_distancia):
            return "vertical"
        return None
    
    def _determinar_posicion_relativa(self, rect1, rect2, direccion_adyacencia):
        """Determina la posición relativa del vecino"""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        if direccion_adyacencia == "horizontal":
            return "izquierda" if x2 < x1 else "derecha"
        else:
            return "arriba" if y2 < y1 else "abajo"
    
    def _guardar_fichas_borde(self, fichas_borde, original_img, output_dir):
        """Guarda imágenes de las fichas de borde con indicadores de vecino"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for ficha in fichas_borde:
            ficha_img = ficha.recortar_ficha(original_img)
            ficha_img = ficha.dibujar_indicador_vecino(ficha_img)
            
            output_path = os.path.join(
                output_dir, 
                f"ficha_borde_{ficha.indice}_vecino_{ficha.posicion_vecino}.jpg"
            )
            cv2.imwrite(output_path, ficha_img)

def obtener_estado(img_path, tamaño_ficha=2900, simulacion=True):
    """Función principal para detectar fichas de dominó en una imagen"""
    # Ejemplo de uso
    detector = DetectorDominoes(umbral_distancia=35)

    # Procesar imagen a blanco y negro
    if not simulacion:
        print("Procesando imagen en modo real...")
    detector.procesar_imagen(img_path, "./Media_Stream/bw_intermediate.jpg", simulacion=simulacion)

    # Detectar fichas
    fichas = detector.detectar_fichas(
        "./Media_Stream/bw_intermediate.jpg",
        tamaño_aprox=tamaño_ficha,
        original_path=img_path,
        output_dir="./Media_Stream/fichas_borde",
        simulacion=simulacion
    )

    print(f"Se detectaron {len(fichas)} fichas de dominó.")

    # Obtener array de datos de fichas en bordes como solicitado
    return [ficha.datos for ficha in fichas if ficha.posicion_vecino is not None]

def Obtener_Ficha_Imagen(path_imagen, coordenadas):
  """
  Recorta una imagen utilizando la librería cv2 según las coordenadas proporcionadas.

  Args:
    path_imagen (str): La ruta al archivo de imagen.
    coordenadas (dict): Un diccionario con las coordenadas del rectángulo
                       a recortar, en el formato {'x1': int, 'y1': int,
                       'x2': int, 'y2': int}.

  Returns:
    numpy.ndarray or None: La imagen recortada como un array NumPy si la
                           operación es exitosa, None si hay algún error.
  """
  try:
    # Leer la imagen utilizando cv2
    img = cv2.imread(path_imagen)

    if img is None:
      print(f"Error: No se pudo leer la imagen en la ruta: {path_imagen}")
      return None

    x1 = coordenadas.get('x1')
    y1 = coordenadas.get('y1')
    x2 = coordenadas.get('x2')
    y2 = coordenadas.get('y2')

    if x1 is None or y1 is None or x2 is None or y2 is None:
      print("Error: El diccionario de coordenadas debe contener las claves 'x1', 'y1', 'x2' e 'y2'.")
      return None

    # Asegurarse de que las coordenadas sean enteros
    x1 = int(x1)
    y1 = int(y1)
    x2 = int(x2)
    y2 = int(y2)

    # Asegurarse de que x1 <= x2 e y1 <= y2
    if x1 > x2 or y1 > y2:
      print("Error: x1 debe ser menor o igual que x2, e y1 debe ser menor o igual que y2.")
      return None

    # Recortar la imagen utilizando slicing de NumPy
    # En OpenCV, las coordenadas se interpretan como [y_inicio:y_fin, x_inicio:x_fin]
    cropped_img = img[y1:y2, x1:x2]
    return cropped_img

  except FileNotFoundError:
    print(f"Error: No se encontró la imagen en la ruta: {path_imagen}")
    return None
  except Exception as e:
    print(f"Ocurrió un error: {e}")
    return None

def obtener_mitad(coordenadas, lado):
  """
  Obtiene la mitad de las coordenadas hacia el lado especificado.

  Args:
    coordenadas (dict): Diccionario con las coordenadas {'x1': ..., 'y1': ..., 'x2': ..., 'y2': ...}.
    lado (str): La dirección hacia la que se quiere la mitad ('izquierda', 'derecha', 'arriba', 'abajo').

  Returns:
    dict: Un nuevo diccionario con las coordenadas de la mitad especificada,
          o el diccionario original si el lado no es válido.
  """
  if lado == "izquierda":
    nueva_coordenadas = {'x1': coordenadas['x1'], 'y1': coordenadas['y1'],
                         'x2': (coordenadas['x1'] + coordenadas['x2']) // 2,
                         'y2': coordenadas['y2']}
    return nueva_coordenadas
  elif lado == "derecha":
    nueva_coordenadas = {'x1': (coordenadas['x1'] + coordenadas['x2']) // 2, 'y1': coordenadas['y1'],
                         'x2': coordenadas['x2'], 'y2': coordenadas['y2']}
    return nueva_coordenadas
  elif lado == "arriba":
    nueva_coordenadas = {'x1': coordenadas['x1'], 'y1': coordenadas['y1'],
                         'x2': coordenadas['x2'], 'y2': (coordenadas['y1'] + coordenadas['y2']) // 2}
    return nueva_coordenadas
  elif lado == "abajo":
    nueva_coordenadas = {'x1': coordenadas['x1'], 'y1': (coordenadas['y1'] + coordenadas['y2']) // 2,
                         'x2': coordenadas['x2'], 'y2': coordenadas['y2']}
    return nueva_coordenadas
  else:
    print(f"Dirección '{lado}' no válida.")
    return coordenadas  # Devolver el diccionario original si el lado no es válido

def obtener_valor_ficha(coordenadas, imagen_path, simulacion=True):
    """
    Obtiene el valor de una mitad de ficha de dominó a partir de sus coordenadas.
    """
    try:
        imagen = cv2.imread(imagen_path)
        if imagen is None:
            print(f"Error: No se pudo cargar la imagen '{imagen_path}'.")
            return -1

        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        x1, y1, x2, y2 = coordenadas['x1'], coordenadas['y1'], coordenadas['x2'], coordenadas['y2']
        recorte = imagen_gris[y1:y2, x1:x2]

        desenfoque = cv2.GaussianBlur(recorte, (3, 3), 0)
        _, umbral = cv2.threshold(desenfoque, 170, 255, cv2.THRESH_BINARY_INV)

        contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        puntos_validos = []
        for contorno in contornos:
            area = cv2.contourArea(contorno)
            #print(f"Area: {area}")
            perimetro = cv2.arcLength(contorno, True)
            #print(f"Perimetro: {perimetro}")
            if perimetro > 0:
                circularidad = 4 * np.pi * area / (perimetro * perimetro)
                #print(f"Circularidad: {circularidad}")
                # Ajusta este umbral de circularidad (un valor cercano a 1 es más circular)
                if simulacion:
                    if 0.5 < circularidad <= 1.0 and 5 < area < 120:
                        puntos_validos.append(contorno)
                else:
                    if 0.5 < circularidad <= 1.0 and 200 < area < 650:
                        puntos_validos.append(contorno)
        
        cv2.imshow("Contornos", umbral)
        cv2.waitKey(0)

        num_puntos = len(puntos_validos)

        if 0 <= num_puntos <= 6:
            return num_puntos
        else:
            return -1

    except FileNotFoundError:
        print(f"Error: No se encontró la imagen '{imagen_path}'.")
        return -1
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return -1
    
def es_horizontal_o_vertical(coordenadas):
    """
    Determina si la ficha es horizontal o vertical basándose en sus coordenadas.

    Args:
        ficha (FichaDomino): Objeto que contiene informacion de la ficha.

    Returns:
        str: "horizontal" si la ficha es horizontal, "vertical" si es vertical.
    """
    x1, y1 = coordenadas['x1'], coordenadas['y1']
    x2, y2 = coordenadas['x2'], coordenadas['y2']
    
    if abs(x2 - x1) > abs(y2 - y1):
        return "horizontal"
    else:
        return "vertical"

    
def obtener_puntuacion_ficha(coordenadas, posicion_vecino, imagen_path, valor_contrario=False, simulacion=True):
    """
    Calcula la puntuación de una ficha de dominó en función de su posición y la
    posición de su vecino.
    
    Args:
        coordenadas (dict): Un diccionario con las coordenadas del rectángulo
                         a recortar, en el formato {'x1': int, 'y1': int,
                         'x2': int, 'y2': int}.
        posicion_vecino (str): La posición del vecino ('izquierda', 'derecha',
                             'arriba', 'abajo').
        valor_contrario (bool): Si es True, se devuelve el valor contrario.
        imagen_path (str): La ruta a la imagen de la ficha de dominó.
    
    Returns:
        int: La puntuación calculada.
    """
    posicion_valor_a_encontrar = ""
    if valor_contrario:
        if posicion_vecino == "izquierda":
            posicion_valor_a_encontrar = "derecha"
        elif posicion_vecino == "derecha":
            posicion_valor_a_encontrar = "izquierda"
        elif posicion_vecino == "arriba":
            posicion_valor_a_encontrar = "abajo"
        elif posicion_vecino == "abajo":
            posicion_valor_a_encontrar = "arriba"
    else:
        posicion_valor_a_encontrar = posicion_vecino
    
    if (posicion_vecino == "izquierda" or posicion_vecino == "derecha") and es_horizontal_o_vertical(coordenadas) == "vertical":
        posicion_valor_a_encontrar = ""
    elif (posicion_vecino == "arriba" or posicion_vecino == "abajo") and es_horizontal_o_vertical(coordenadas) == "horizontal":
        posicion_valor_a_encontrar = ""

    if posicion_valor_a_encontrar == "":
        print("Ficha de jugador")
        puntuacion = []
        nueva_coordenadas = obtener_mitad(coordenadas, "arriba")
        puntuacion.append(obtener_valor_ficha(nueva_coordenadas, imagen_path, simulacion))
        nueva_coordenadas = obtener_mitad(coordenadas, "abajo")
        puntuacion.append(obtener_valor_ficha(nueva_coordenadas, imagen_path, simulacion))
        return puntuacion
    else:
        nueva_coordenadas = obtener_mitad(coordenadas, posicion_valor_a_encontrar)
        return obtener_valor_ficha(nueva_coordenadas, imagen_path, simulacion)

def obtener_fichas_jugador(img_path, tamaño_ficha, simulacion=True):
    """Función secundaria para detectar fichas de dominó en una imagen"""
    # Ejemplo de uso
    detector = DetectorDominoes(umbral_distancia=35)

    # Procesar imagen a blanco y negro
    detector.procesar_imagen(img_path, "./Media_Stream/bw_intermediate_player.jpg", simulacion=simulacion)
 
    # Detectar fichas
    fichas = detector.detectar_fichas(
        "./Media_Stream/bw_intermediate_player.jpg",
        tamaño_aprox=tamaño_ficha,
        original_path=img_path,
        output_dir="./Media_Stream/fichas_borde_jugador",
        simulacion=simulacion
    )

    print(f"Se detectaron {len(fichas)} fichas de dominó.")

    # Obtener array de datos de fichas en bordes como solicitado
    return [ficha.datos for ficha in fichas]

def obtener_estado_completo(img_path_tablero, img_path_jugador, tamaño_ficha=2900, simulacion=True):
    """
    Función para obtener el estado completo del juego de dominó.
    """
    fichas_borde_data = obtener_estado(img_path_tablero, tamaño_ficha, simulacion=simulacion)

    posibles_fichas = []

    print("Fichas en bordes detectadas:")
    for i, ficha_data in enumerate(fichas_borde_data):
        print(f"Ficha {i}:")
        print(f"  Coordenadas: {ficha_data[0]}")
        print(f"  Vecino: {ficha_data[1]}")
        print(f"  Número de vecinos: {ficha_data[2]}")

        img = Obtener_Ficha_Imagen(img_path_tablero, ficha_data[0])

        puntuacion = obtener_puntuacion_ficha(ficha_data[0], ficha_data[1],img_path_tablero, True, simulacion=simulacion)
        print(f"  Puntuación: {puntuacion}")
        # Añadir la puntuación a la lista de datos de la ficha
        fichas_borde_data[i].append(puntuacion)

        if isinstance(puntuacion, list) and len(puntuacion) == 2:
            # Si la puntuación es una lista, es una ficha doble
            posibles_fichas.append(puntuacion[0])
        elif isinstance(puntuacion, int):
            posibles_fichas.append(puntuacion)

    fichas_jugador_data = obtener_fichas_jugador(img_path_jugador, tamaño_ficha, simulacion=simulacion)

    print("Fichas del jugador disponibles:")
    for i, ficha_data in enumerate(fichas_jugador_data):
        print(f"Ficha {i}:")
        print(f"  Coordenadas: {ficha_data[0]}")
        puntuacion = obtener_puntuacion_ficha(ficha_data[0], ficha_data[1],img_path_jugador, True, simulacion=simulacion)
        print(f"  Puntuación: {puntuacion[0]}, {puntuacion[1]}")
        # Añadir la puntuación a la lista de datos de la ficha
        fichas_jugador_data[i].append(puntuacion)

        img = Obtener_Ficha_Imagen(img_path_jugador, ficha_data[0])

    return fichas_borde_data, fichas_jugador_data, posibles_fichas

if __name__ == "__main__":
    # Prueba con imagen real de ejemplo
    #img_path = "./Media_Example/Ejemplo-tablero-real.jpg"

    image = img = cv2.imread("./Media_Example/Ejemplo-tablero-real.jpg")
        
    # Separamos la imagen por la mitad (parte de arriba y de abajo) y lo guardamos en dos archivos
    if image is not None:
        # La imagen debe ser rgb
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cv2.imwrite("./Media_Stream/imagen_tablero.png", image)
        height, width, _ = image.shape
        # La parte de arriba debe ser dos tercios de la imagen
        top_two_thirds = image[:2*height//3, :]
        bottom_one_third = image[2*height//3:, :]
        cv2.imwrite("./Media_Stream/parte_superior.png", top_two_thirds)
        cv2.imwrite("./Media_Stream/parte_inferior.png", bottom_one_third)
        print("Size parte superior:", top_two_thirds.shape)
        print("Size parte inferior:", bottom_one_third.shape)

    tamaño_ficha = 32500

    # Obtenemos coordenada
    fichas_borde_data, fichas_jugador_data, posibles_fichas = obtener_estado_completo("./Media_Stream/parte_superior.png", "./Media_Stream/parte_inferior.png", tamaño_ficha=tamaño_ficha, simulacion=False)

    print("Posibles fichas en el tablero:", posibles_fichas)

    print("Fichas del jugador ordenadas de izquierda a derecha:")   
    for i, ficha_data in enumerate(fichas_jugador_data):
        print(f"Ficha {i}: Coordenadas: {ficha_data[0]}, Puntuación: {ficha_data[3]}")


    # fichas_borde_data = obtener_estado(img_path, tamaño_ficha=32500, simulacion=False)

    # posibles_fichas = []

    # print("Fichas en bordes detectadas:")
    # for i, ficha_data in enumerate(fichas_borde_data):
    #     print(f"Ficha {i}:")
    #     print(f"  Coordenadas: {ficha_data[0]}")
    #     print(f"  Vecino: {ficha_data[1]}")
    #     print(f"  Número de vecinos: {ficha_data[2]}")

    #     img = Obtener_Ficha_Imagen(img_path, ficha_data[0])

    #     puntuacion = obtener_puntuacion_ficha(ficha_data[0], ficha_data[1],img_path, True, simulacion=False)
    #     print(f"  Puntuación: {puntuacion}")
    #     # Añadir la puntuación a la lista de datos de la ficha
    #     fichas_borde_data[i].append(puntuacion)

    #     if isinstance(puntuacion, list) and len(puntuacion) == 2:
    #         # Si la puntuación es una lista, es una ficha doble
    #         posibles_fichas.append(puntuacion[0])
    #     elif isinstance(puntuacion, int):
    #         posibles_fichas.append(puntuacion)
