import os
import sys
import time
import json
import numpy as np
import sympy as sp
from sympy import nsolve
from Hardware_Controllers.drivers.GestorInstancies import GestorInstancies
from Hardware_Controllers.drivers.initRobotComponents import init_robot_components

def find_project_root(current_path):
    """
    Busca el directori arrel del projecte pujant per l'estructura de directoris
    fins que troba el fitxer '.project_root'.
    """
    while True:
        if os.path.exists(os.path.join(current_path, '.project_root')):
            return current_path
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path: # Arribat a la rel de l'arbre de directoris
            raise FileNotFoundError("No s'ha pogut trobar el fitxer '.project_root' en cap directori ascendent.")
        current_path = parent_path

class ScaraControllerIntermediary:
    def __init__(self):
        self.joint_angles = {
            'joint1': 0.0,
            'joint2': 0.0,
            'joint3': 0.0,
            'joint4': 0.0
        }

        try:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = find_project_root(current_script_dir)
            print(f"Arrel del projecte trobada a: {project_root}")

            CONFIG_FILE_PATH = os.path.join(project_root, 'config', 'robot_config.json')

        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR inesperat al localitzar l'arrel del projecte o la configuració: {e}")
            sys.exit(1)

        print("\n--- Càrrega de la configuració des del fitxer JSON ---")
        config_data = {}
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"Configuració carregada amb èxit des de: {CONFIG_FILE_PATH}\n")
        except FileNotFoundError:
            print(f"ERROR: El fitxer de configuració '{CONFIG_FILE_PATH}' no s'ha trobat.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"ERROR: El fitxer '{CONFIG_FILE_PATH}' no és un JSON vàlid. Revisa la seva sintaxi.")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR inesperat al carregar la configuració: {e}")
            sys.exit(1)

        with GestorInstancies() as gestor_instancies:
            try:
                # Crida a la funció centralitzada d'inicialització
                # Aquesta funció retorna un diccionari amb totes les instàncies inicialitzades
                instantiated_components = init_robot_components(gestor_instancies, config_data)

                # Controladors de percepció i interacció
                self.camera = instantiated_components.get(config_data.get("camera", {}).get("nom")) # Usa el nom del JSON
                self.microphone = instantiated_components.get(config_data.get("microphone", {}).get("nom")) # Usa el nom del JSON
                self.altaveu = instantiated_components.get(config_data.get("altaveu", {}).get("nom")) # Usa el nom del JSON
                
                # Controladors de moviment
                self.motor_base = instantiated_components.get(config_data.get("motors_pas_a_pas", [{}])[0].get("nom")) # Assumint el primer motor_pas_a_pas és el de la base
                self.motor_articulacio_secundaria = instantiated_components.get(config_data.get("motors_pas_a_pas", [{}, {}])[1].get("nom")) # Assumint el segon motor_pas_a_pas és l'articulació secundaria
                self.motor_eix_z = instantiated_components.get(config_data.get("motors_pas_a_pas", [{}, {}, {}])[2].get("nom")) # Assumint el tercer motor_pas_a_pas és l'eix Z
                
                self.servomotor_canell = instantiated_components.get(config_data.get("servomotor", {}).get("nom")) # Usa el nom del JSON
                self.electroiman = instantiated_components.get(config_data.get("electroiman", {}).get("nom")) # Usa el nom del JSON
                
                # Gestors i controladors superiors
                self.file_manager = instantiated_components.get(config_data.get("file_manager", {}).get("nom")) # Usa el nom del JSON
                self.scara_controller = instantiated_components.get(config_data.get("scara_controller", {}).get("nom")) # Usa el nom del JSON
            except Exception as e:
                print(f"\nS'ha produït un error inesperat durant l'execució: {e}")

    def move_posicion_inicial(self):
        """
        Mueve el robot a una posición para tomar una foto inicial.
        """
        angulo_joint1 = -90
        angulo_joint2 = 0
        angulo_joint3 = self.joint_angles['joint3']
        angulo_joint4 = 0

        self.scara_controller.mou_a_posicio_eixos(angulo_joint1, angulo_joint2, angulo_joint3, angulo_joint4, velocitat_index=0)

        # Actualizar los ángulos del robot
        self.joint_angles['joint1'] = angulo_joint1
        self.joint_angles['joint2'] = angulo_joint2
        self.joint_angles['joint3'] = angulo_joint3
        self.joint_angles['joint4'] = angulo_joint4
        
        time.sleep(1)
    
    def move_posicion_recta(self):
        """
        Mueve el robot a una posición recta
        """
        angulo_joint1 = 0
        angulo_joint2 = 0
        angulo_joint3 = self.joint_angles['joint3']
        angulo_joint4 = 0

        self.scara_controller.mou_a_posicio_eixos(angulo_joint1, angulo_joint2, angulo_joint3, angulo_joint4, velocitat_index=0)

        # Actualizar los ángulos del robot
        self.joint_angles['joint1'] = angulo_joint1
        self.joint_angles['joint2'] = angulo_joint2
        self.joint_angles['joint3'] = angulo_joint3
        self.joint_angles['joint4'] = angulo_joint4
        
        time.sleep(1)
    
    def obtener_foto(self):
        print("Obteniendo foto del robot (simulación)...")
        # Aquí iría la lógica para obtener una foto del robot en simulación
        if self.camera:
            print(f"Càmera disponible: {self.camera.nom_camera}")
            # Aquí podries cridar mètodes de la càmera, per exemple:
            # time.sleep(1)
            # print("Previsualitzant càmera per 5 segons...")
            # camera.start_preview()
            # time.sleep(5)
            # camera.stop_preview()
            # print("Previsualització finalitzada.")
        else:
            print("La càmera no s'ha inicialitzat correctament o no està disponible.")

    
    def move_domino(self, px, py, roll, yaw, rotacion=0):
        if self.clientID == -1:
            print("No conectado a CoppeliaSim.")
            return

        # Convertir a radianes
        roll = np.deg2rad(roll)
        yaw = np.deg2rad(yaw)

        # Matriz de rotación roll (X)
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(roll), -np.sin(roll)],
            [0, np.sin(roll), np.cos(roll)]
        ])

        # Matriz de rotación yaw (Z)
        Rz = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw),  np.cos(yaw), 0],
            [0, 0, 1]
        ])

        # Rotación compuesta
        R = Rz @ Rx

        # Offset ventosa (Z-)
        offset_local = np.array([0, 0, -self.dventosa])
        offset_global = R @ offset_local

        # Posición corregida (XY únicamente)
        px_corr = px + offset_global[0]
        py_corr = py + offset_global[1]

        # Verificación de alcance
        alcance_max = 0.26 + 0.1425
        r = np.hypot(px_corr, py_corr)
        if r > alcance_max:
            print(f"Error: el punto ({px_corr:.3f}, {py_corr:.3f}) está fuera del alcance del robot ({alcance_max:.3f} m).")
            return

        d3_fijo = self.joint_angles['joint3']  # No se moverá
        theta1, theta2 = sp.symbols('theta1 theta2')

        mbee_eval = self.mbee_symbolic.subs({
            self.lc: 0.2,
            self.la: 0.26,
            self.lb: 0.1425,
            self.l4: 0.0981,
            self.theta1: theta1,
            self.theta2: theta2,
            self.theta4: 0,
            self.d3: d3_fijo
        }).evalf()

        equations = [
            sp.Eq(mbee_eval[0, 3], px_corr),
            sp.Eq(mbee_eval[1, 3], py_corr)
        ]

        # Estimación inicial por geometría inversa simple
        try:
            cos_theta2 = (r**2 - 0.26**2 - 0.1425**2) / (2 * 0.26 * 0.1425)
            if abs(cos_theta2) > 1:
                print("Error: configuración geométrica imposible (cosθ2 fuera de [-1, 1]).")
                return

            theta2_guess = np.arccos(cos_theta2)
            theta1_guess = np.arctan2(py_corr, px_corr) - np.arctan2(0.1425 * np.sin(theta2_guess), 0.26 + 0.1425 * np.cos(theta2_guess))

            initial_guess = (theta1_guess, theta2_guess)
        except Exception as e:
            print("Error al calcular estimación inicial:", e)
            return

        try:
            sol = nsolve(equations, (theta1, theta2), initial_guess)
            th1_sol, th2_sol = sol
            print(f"Solución encontrada: θ1={th1_sol.evalf():.3f}, θ2={th2_sol.evalf():.3f}")

            angulo_joint1 = np.rad2deg(th1_sol)
            angulo_joint2 = np.rad2deg(th2_sol)
            angulo_joint3 = self.joint_angles['joint3']
            angulo_joint4 = -(angulo_joint1 + angulo_joint2)+rotacion

            self.scara_controller.mou_a_posicio_eixos(angulo_joint1, angulo_joint2, angulo_joint3, angulo_joint4, velocitat_index=0)

            # Actualizar los ángulos del robot
            self.joint_angles['joint1'] = angulo_joint1
            self.joint_angles['joint2'] = angulo_joint2
            self.joint_angles['joint3'] = angulo_joint3
            self.joint_angles['joint4'] = angulo_joint4

            print(f"✔️ Movimiento exitoso a XY ({px:.3f}, {py:.3f}).")
            print(f"Ángulos (grados): 01: {angulo_joint1:.3f}, 02: {angulo_joint2:.3f}, 03: {angulo_joint3:.3f}, 04: {angulo_joint4:.3f}")

        except Exception as e:
            print("❌ Error al resolver cinemática inversa en XY:", e)

        time.sleep(1)
    
    def coger_ficha(self):
        print("Cogiendo ficha...")

        distancia_de_seguridad = 0.05  # Distancia de seguridad para evitar colisiones

        # Bajamos el robot a una posición segura para coger la ficha
        self.scara_controller.mou_a_posicio_eixos(
            self.joint_angles['joint1'],
            self.joint_angles['joint2'],
            distancia_de_seguridad,  # Bajamos un poco
            self.joint_angles['joint4'],
            velocitat_index=0
        )

        time.sleep(2)

        self.scara_controller.electroiman.activar()  # Activamos el electroimán para coger la ficha
        time.sleep(1)

        # Subimos el robot a la posición original
        self.scara_controller.mou_a_posicio_eixos(
            self.joint_angles['joint1'],
            self.joint_angles['joint2'],
            self.joint_angles['joint3'],  # Volvemos a la altura original
            self.joint_angles['joint4'],
            velocitat_index=0
        )

        time.sleep(2)

    
    def soltar_ficha(self):
        distancia_de_seguridad = 0.05  # Distancia de seguridad para evitar colisiones

        # Bajamos el robot a una posición segura para coger la ficha
        self.scara_controller.mou_a_posicio_eixos(
            self.joint_angles['joint1'],
            self.joint_angles['joint2'],
            distancia_de_seguridad,  # Bajamos un poco
            self.joint_angles['joint4'],
            velocitat_index=0
        )

        time.sleep(2)

        self.scara_controller.electroiman.desactivar()  # Desactivamos el electroimán para soltar la ficha
        time.sleep(1)

        # Subimos el robot a la posición original
        self.scara_controller.mou_a_posicio_eixos(
            self.joint_angles['joint1'],
            self.joint_angles['joint2'],
            self.joint_angles['joint3'],  # Volvemos a la altura original
            self.joint_angles['joint4'],
            velocitat_index=0
        )

        time.sleep(2)

    def disconnect(self):
        print("Desconectando el robot (simulación)...")
        # Aquí iría la lógica para desconectar el robot en simulación
        # Por ejemplo, cerrar la conexión con los motores y sensores
        time.sleep(1)
