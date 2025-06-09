from Detectar_Domino import obtener_estado_completo, es_horizontal_o_vertical
from Reconocimiento_Voz import escuchar_y_detectar_comando_continuo
import cv2
from Domibot import DominoRobotController, pixel_to_world_linear
import time
from Controlador_coordenadas import bbox_center, calcular_coordenada_juego, calcular_rotacion, obtener_fichas_posibles_donde_jugar, ordenar_fichas_jugador_por_coordenadas, obtener_valores_comunes_y_coincidencia

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
    print("Posibles fichas en el tablero:", posibles_fichas)
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
            direccion = ""
            if fichas_posibles:
                if len(fichas_posibles) > 1:
                    confirmar_posicion = True
                else:
                    confirmar_posicion = False

                print(f"Posibles posiciones para jugar la ficha {decision_jugador}: {fichas_posibles}")
                robot_controller.move_posicion_recta()
                time.sleep(2)

                # Solicitar al jugador posición relativa a la ficha y orientación
                coordenada_calculada = calcular_coordenada_juego(fichas_posibles[0])

                # Elegir direccion si hay más de una
                if len(coordenada_calculada) > 1:
                    print(f"Hay varias posiciones posibles para jugar la ficha {decision_jugador}.")
                    print(f"Posiciones posibles: {coordenada_calculada.keys()}")
                    # Pedir al jugador que elija una posición
                    direccion = input("¿En qué dirección quieres jugar la ficha? (izquierda, derecha, arriba, abajo): ")
                    if direccion in coordenada_calculada:
                        coordenada_calculada = coordenada_calculada[direccion]
                    else:
                        print(f"Dirección {direccion} no válida. Usando la primera posición disponible.")
                        coordenada_calculada = list(coordenada_calculada.values())[0]
                else:
                    print(f"Solo hay una posición posible para jugar la ficha {coordenada_calculada.keys()}.")
                    direccion = list(coordenada_calculada.keys())[0]
                    coordenada_calculada = list(coordenada_calculada.values())[0]

                real_x_posicion, real_y_posicion = pixel_to_world_linear(coordenada_calculada[0], coordenada_calculada[1])
                print(f"Coordenadas calculadas para jugar la ficha: {coordenada_calculada[0], coordenada_calculada[1]}")
                print(f"Coordenadas reales para jugar la ficha: ({real_x_posicion}, {real_y_posicion})")
                rotacion = calcular_rotacion(fichas_jugador_data[numero_ficha][3], direccion, decision_jugador)
                print(f"Rotacion: {rotacion}")
                robot_controller.move_domino(px=real_x_posicion, py=real_y_posicion, roll=0, yaw=0, rotacion=rotacion)
                time.sleep(2)
                # Soltar ficha
                robot_controller.soltar_ficha()
                print("Ficha soltada en la posición correcta.")
                time.sleep(2)
            else:
                print(f"No hay posiciones disponibles para jugar la ficha {decision_jugador}.")

        else:
            print(f"El jugador ha seleccionado una ficha incorrecta. Las puntuaciones posibles son: {posibles_fichas}")

    time.sleep(3)

    # Mover a posición de juego
    robot_controller.move_posicion_recta()

    time.sleep(2)
    
    robot_controller.disconnect()
else:
    print("No se pudo inicializar el controlador del robot.")