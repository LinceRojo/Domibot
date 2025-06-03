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
    
    def procesar_imagen(self, original_path, bw_output_path):
        """Convierte la imagen original a blanco y negro para procesamiento"""
        img = cv2.imread(original_path)
        if img is None:
            raise FileNotFoundError(f"No se pudo leer la imagen en {original_path}")
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 210])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        cv2.imwrite(bw_output_path, white_mask)
        return white_mask
    
    def detectar_fichas(self, mascara_path, tamaño_aprox, original_path, output_dir="fichas_borde"):
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

def obtener_estado(img_path):
    """Función principal para detectar fichas de dominó en una imagen"""
    # Ejemplo de uso
    detector = DetectorDominoes(umbral_distancia=35)

    # Procesar imagen a blanco y negro
    detector.procesar_imagen(img_path, "bw_intermediate.jpg")

    # Detectar fichas
    fichas = detector.detectar_fichas(
        "bw_intermediate.jpg",
        tamaño_aprox=2900,
        original_path=img_path,
        output_dir="fichas_borde"
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

def obtener_valor_ficha(coordenadas, imagen_path):
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
            # print(f"Area: {area}")
            perimetro = cv2.arcLength(contorno, True)
            # print(f"Perimetro: {perimetro}")
            if perimetro > 0:
                circularidad = 4 * np.pi * area / (perimetro * perimetro)
                # Ajusta este umbral de circularidad (un valor cercano a 1 es más circular)
                if 0.5 < circularidad <= 1.0 and 5 < area < 120:
                    puntos_validos.append(contorno)
        
        # cv2.imshow("Contornos", umbral)
        # cv2.waitKey(0)

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
    
def obtener_puntuacion_ficha(coordenadas, posicion_vecino, imagen_path, valor_contrario=False):
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
    
    if posicion_valor_a_encontrar == "":
        print("Ficha de jugador")
        puntuacion = []
        nueva_coordenadas = obtener_mitad(coordenadas, "arriba")
        puntuacion.append(obtener_valor_ficha(nueva_coordenadas, imagen_path))
        nueva_coordenadas = obtener_mitad(coordenadas, "abajo")
        puntuacion.append(obtener_valor_ficha(nueva_coordenadas, imagen_path))
        return puntuacion
    else:
        nueva_coordenadas = obtener_mitad(coordenadas, posicion_valor_a_encontrar)
        return obtener_valor_ficha(nueva_coordenadas, imagen_path)

def obtener_fichas_jugador(img_path):
    """Función secundaria para detectar fichas de dominó en una imagen"""
    # Ejemplo de uso
    detector = DetectorDominoes(umbral_distancia=15)

    # Procesar imagen a blanco y negro
    detector.procesar_imagen(img_path, "bw_intermediate_player.jpg")

    # Detectar fichas
    fichas = detector.detectar_fichas(
        "bw_intermediate_player.jpg",
        tamaño_aprox=3900,
        original_path=img_path,
        output_dir="fichas_borde_jugador"
    )

    print(f"Se detectaron {len(fichas)} fichas de dominó.")

    # Obtener array de datos de fichas en bordes como solicitado
    return [ficha.datos for ficha in fichas]