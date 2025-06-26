import cv2
import time
from Virtual_Controllers.Detectar_Domino import obtener_estado_completo
from Virtual_Controllers.Reconocimiento_Voz import escuchar_y_detectar_comando_continuo
from Virtual_Controllers.Domibot import DominoRobotController, pixel_to_world_linear
from Virtual_Controllers.Controlador_coordenadas import bbox_center, calcular_coordenada_juego, calcular_rotacion, obtener_fichas_posibles_donde_jugar, ordenar_fichas_jugador_por_coordenadas, obtener_valores_comunes_y_coincidencia
from Hardware_Controllers.ScaraControllerIntermediary import ScaraControllerIntermediary

# ------------ USO DEL ROBOT DOMINO -------------------

## Solicitamos al usuario si quiere jugar en simulación o con el robot real
simulacion = input("¿Quieres jugar en simulación? (s/n): ").strip().lower()
if simulacion == 's':
    print("Iniciando en modo simulación...")
    simulacion = True
else:
    print("Iniciando en modo real...")
    simulacion = False
    
if simulacion:
    robot_controller_coppelia = DominoRobotController(port=19999)    
    if robot_controller_coppelia.clientID == -1:
        raise Exception("No se pudo conectar al robot en modo simulación.")
else:
    robot_controller_raspberry = ScaraControllerIntermediary()
    print("Prueba")


## Comienza la logica del juego
continuar = True

while continuar:
    # Movemos a posición inicial
    if simulacion:
        robot_controller_coppelia.move_posicion_inicial()
    else:
        robot_controller_raspberry.move_posicion_inicial()

    time.sleep(2)
        
    # Obtener foto
    if simulacion:
        image = robot_controller_coppelia.obtener_foto()
    else:
        image = img = cv2.imread("./Media_Example/Ejemplo-tablero-real.jpg")
        #image = robot_controller_raspberry.obtener_foto()
        
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

    if simulacion:
        robot_controller_coppelia.move_posicion_recta()
    else:
        robot_controller_raspberry.move_posicion_recta()

    time.sleep(2)

    if simulacion:
        tamaño_ficha = 2900
    else:
        tamaño_ficha = 32500

    # Obtenemos coordenada
    fichas_borde_data, fichas_jugador_data, posibles_fichas = obtener_estado_completo("./Media_Stream/parte_superior.png", "./Media_Stream/parte_inferior.png", tamaño_ficha=tamaño_ficha, simulacion=simulacion)

    print("Posibles fichas en el tablero:", posibles_fichas)
    fichas_jugador_data = ordenar_fichas_jugador_por_coordenadas(fichas_jugador_data)

    print("Fichas del jugador ordenadas de izquierda a derecha:")   
    for i, ficha_data in enumerate(fichas_jugador_data):
        print(f"Ficha {i}: Coordenadas: {ficha_data[0]}, Puntuación: {ficha_data[3]}")

    ficha_correcta = False
    while ficha_correcta == False:
        if simulacion:
            # Preguntar al jugador qué ficha quiere jugar, con una entrada de texto
            numero_ficha = input("¿Qué ficha quieres jugar? (Introduce el número de la ficha): ")
            numero_ficha = int(numero_ficha) if numero_ficha.isdigit() else None
        else:
            # Escuchar el comando de voz del jugador
            numero_ficha, texto = escuchar_y_detectar_comando_continuo("¿Qué ficha quieres jugar?")
            print(f"Comando detectado: {numero_ficha}, Texto completo: {texto}")
            numero_ficha = int(numero_ficha) if numero_ficha.isdigit() else None
            if numero_ficha is None:
                print("No se ha detectado un número de ficha válido. Inténtalo de nuevo.")
                continue

        # Validar que el número de ficha es válido
        hay_coincidencia, puntuaciones_posibles = obtener_valores_comunes_y_coincidencia(fichas_jugador_data[numero_ficha][3], posibles_fichas)
        if hay_coincidencia:
            ficha_correcta = True

            print(f"El jugador ha decidido jugar la ficha con puntuación {numero_ficha}.")
            center_x, center_y = bbox_center(fichas_jugador_data[numero_ficha][0])
            
            ## Calcular coordenadas reales
            if simulacion:
                offset = 320
                print(f"Ficha {i} del jugador: Coordenadas del centro (u, v): ({center_x}, {center_y+offset})")
                real_x, real_y = pixel_to_world_linear(center_x, center_y+offset)
                print(f"Ficha {i} del jugador: Coordenadas reales (x, y): ({real_x}, {real_y})")
            else:
                offset = 822
                print(f"Ficha {i} del jugador: Coordenadas del centro (u, v): ({center_x}, {center_y+offset})")
                real_x, real_y = pixel_to_world_linear(center_x, center_y+offset, img_resolution=(3280, 2464), x_limits=(0.50, 0.10), y_limits=(0.30, -0.30))
                print(f"Ficha {i} del jugador: Coordenadas reales (x, y): ({real_x}, {real_y})")
                
            if simulacion:
                robot_controller_coppelia.move_domino(px=real_x, py=real_y, roll=0, yaw=90)
            else:
                robot_controller_raspberry.move_domino(px=real_x, py=real_y, roll=0, yaw=90)
            
            time.sleep(2)
            
            if simulacion:
                robot_controller_coppelia.coger_ficha()
            else:
                robot_controller_raspberry.coger_ficha()

            time.sleep(2)

            if len(puntuaciones_posibles) > 1:
                puntuacion_valida = False
                while not puntuacion_valida:
                    print(f"El jugador ha seleccionado una ficha con múltiples puntuaciones posibles: {puntuaciones_posibles}.")
                    # Pedimos al jugador que confirme el valor de la ficha

                    if simulacion:
                        # Pedir al jugador que introduzca el valor de la ficha
                        decision_jugador = input(f"¿Cuál es el valor de la ficha que quieres jugar? (Posibles valores: {puntuaciones_posibles}): ")
                    else:
                        # Escuchar el comando de voz del jugador
                        decision_jugador, texto = escuchar_y_detectar_comando_continuo("¿Cuál es el valor de la ficha que quieres jugar?")
                        print(f"Comando detectado: {decision_jugador}, Texto completo: {texto}")
                    
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

                if simulacion:
                    robot_controller_coppelia.move_posicion_recta()
                else:
                    robot_controller_raspberry.move_posicion_recta()

                time.sleep(2)

                # Solicitar al jugador posición relativa a la ficha y orientación
                if simulacion:
                    coordenada_calculada = calcular_coordenada_juego(fichas_posibles[0])
                else:
                    coordenada_calculada = calcular_coordenada_juego(fichas_posibles[0], ANCHURA_FICHA=135, LONGITUD_FICHA=270)

                # Elegir direccion si hay más de una
                if len(coordenada_calculada) > 1:
                    print(f"Hay varias posiciones posibles para jugar la ficha {decision_jugador}.")
                    print(f"Posiciones posibles: {coordenada_calculada.keys()}")

                    # Pedir al jugador que elija una posición
                    if simulacion:
                        direccion = input("¿En qué dirección quieres jugar la ficha? (izquierda, derecha, arriba, abajo): ")
                    else:
                        # Escuchar el comando de voz del jugador
                        direccion, texto = escuchar_y_detectar_comando_continuo("¿En qué dirección quieres jugar la ficha? (izquierda, derecha, arriba, abajo)")
                        print(f"Comando detectado: {direccion}, Texto completo: {texto}")
                    
                    if direccion in coordenada_calculada:
                        coordenada_calculada = coordenada_calculada[direccion]
                    else:
                        print(f"Dirección {direccion} no válida. Usando la primera posición disponible.")
                        coordenada_calculada = list(coordenada_calculada.values())[0]
                else:
                    print(f"Solo hay una posición posible para jugar la ficha {coordenada_calculada.keys()}.")
                    direccion = list(coordenada_calculada.keys())[0]
                    coordenada_calculada = list(coordenada_calculada.values())[0]

                # Calcular coordenadas reales
                if simulacion:
                    real_x_posicion, real_y_posicion = pixel_to_world_linear(coordenada_calculada[0], coordenada_calculada[1])
                    print(f"Coordenadas calculadas para jugar la ficha: {coordenada_calculada[0], coordenada_calculada[1]}")
                    print(f"Coordenadas reales para jugar la ficha: ({real_x_posicion}, {real_y_posicion})")
                    rotacion = calcular_rotacion(fichas_jugador_data[numero_ficha][3], direccion, decision_jugador)
                    print(f"Rotacion: {rotacion}")
                else:
                    real_x_posicion, real_y_posicion = pixel_to_world_linear(coordenada_calculada[0], coordenada_calculada[1], img_resolution=(3280, 2464), x_limits=(0.50, 0.10), y_limits=(0.30, -0.30))
                    print(f"Coordenadas calculadas para jugar la ficha: {coordenada_calculada[0], coordenada_calculada[1]}")
                    print(f"Coordenadas reales para jugar la ficha: ({real_x_posicion}, {real_y_posicion})")
                    rotacion = calcular_rotacion(fichas_jugador_data[numero_ficha][3], direccion, decision_jugador)
                    print(f"Rotacion: {rotacion}")
                
                # Mover a la posición de juego
                if simulacion:
                    robot_controller_coppelia.move_domino(px=real_x_posicion, py=real_y_posicion, roll=0, yaw=0, rotacion=rotacion)
                else:
                    robot_controller_raspberry.move_domino(px=real_x_posicion, py=real_y_posicion, roll=0, yaw=0, rotacion=rotacion)
                
                time.sleep(2)

                # Soltar ficha
                if simulacion:
                    robot_controller_coppelia.soltar_ficha()
                else:
                    robot_controller_raspberry.soltar_ficha()

                print("Ficha soltada en la posición correcta.")
                time.sleep(2)
            else:
                print(f"No hay posiciones disponibles para jugar la ficha {decision_jugador}.")
        else:
            print(f"El jugador ha seleccionado una ficha incorrecta. Las puntuaciones posibles son: {posibles_fichas}")

    time.sleep(3)

    # Mover a posición de juego
    if simulacion:
        robot_controller_coppelia.move_posicion_recta()
    else:
        robot_controller_raspberry.move_posicion_recta()

    time.sleep(2)

    if (input("Quieres jugar otra ficha? (Presiona Enter para continuar o escribe 'n' para terminar): ") == 'n'):
        continuar = False


if simulacion:
    robot_controller_coppelia.disconnect()
else:
    robot_controller_raspberry.disconnect()

print("Juego terminado. El robot ha jugado la ficha correctamente.")