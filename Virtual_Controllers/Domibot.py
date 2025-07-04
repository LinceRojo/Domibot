#!/usr/bin/env python
# coding: utf-8

import numpy as np
import sympy as sp
from sympy import N, nsolve
from sympy.physics.vector import init_vprinting
from sympy.physics.mechanics import dynamicsymbols
import Virtual_Controllers.sim as sim
import time
import matplotlib.pyplot as plt
from Virtual_Controllers.Detectar_Domino import obtener_estado, Obtener_Ficha_Imagen, obtener_puntuacion_ficha, obtener_fichas_jugador


class DominoRobotController:
    def __init__(self, port=19999):
        init_vprinting(use_latex='mathjax', pretty_print=False)
        self._define_symbols()
        self._initialize_transformation_matrices()
        self._substitute_robot_params()

        self.clientID = self._connect_coppelia(port)
        if self.clientID != -1:
            self._get_joint_handles()
            self._get_suction_cup_handle()
            self._get_camera_handle()
        else:
            print("Error: No se pudo conectar a CoppeliaSim. Las funciones del robot no estarán disponibles.")

        self.dventosa = 0.011

        # Estado interno de ángulos de joints en radianes
        self.joint_angles = {
            'joint1': 0.0,
            'joint2': 0.0,
            'joint3': 0.0,
            'joint4': 0.0
        }

        # Sincronizar estado interno leyendo ángulos reales al inicio
        #if self.clientID != -1:
        #    self._update_joint_angles_from_robot()

    def _define_symbols(self):
        (self.theta1, self.theta2, self.theta3, self.theta4, self.lc, self.la,
         self.lb, self.l4, self.d3, self.theta, self.alpha, self.a, self.d) = \
            dynamicsymbols('theta1 theta2 theta3 theta4 lc la lb l4 d3 theta alpha a d')

    def _initialize_transformation_matrices(self):
        rot = sp.Matrix([[sp.cos(self.theta), -sp.sin(self.theta)*sp.cos(self.alpha), sp.sin(self.theta)*sp.sin(self.alpha)],
                         [sp.sin(self.theta), sp.cos(self.theta)*sp.cos(self.alpha), -sp.cos(self.theta)*sp.sin(self.alpha)],
                         [0, sp.sin(self.alpha), sp.cos(self.alpha)]])
        trans = sp.Matrix([self.a*sp.cos(self.theta), self.a*sp.sin(self.theta), self.d])
        last_row = sp.Matrix([[0, 0, 0, 1]])
        self.m_generic = sp.Matrix.vstack(sp.Matrix.hstack(rot, trans), last_row)
        self.m01 = self.m_generic.subs({self.theta: self.theta1, self.d: self.lc, self.a: self.la, self.alpha: 0})
        self.m12 = self.m_generic.subs({self.theta: self.theta2, self.d: 0, self.a: self.lb, self.alpha: 180 * np.pi / 180})
        self.m12[0, 2] = 0
        self.m12[1, 2] = 0
        self.m12[2, 1] = 0
        self.m23 = self.m_generic.subs({self.theta: 0, self.d: self.d3, self.a: 0, self.alpha: 0 * np.pi / 180})
        self.m34 = self.m_generic.subs({self.theta: self.theta4, self.d: self.l4, self.a: 0, self.alpha: 180 * np.pi / 180})
        self.m34[0, 2] = 0
        self.m34[1, 2] = 0
        self.m34[2, 1] = 0
        m04_unsimplified = (self.m01 * self.m12 * self.m23 * self.m34)
        self.mbee_symbolic = sp.Matrix([
            [sp.trigsimp(m04_unsimplified[0, 0].simplify()), sp.trigsimp(m04_unsimplified[0, 1].simplify()), (m04_unsimplified[0, 2].simplify()), sp.trigsimp(m04_unsimplified[0, 3].simplify())],
            [sp.trigsimp(m04_unsimplified[1, 0].simplify()), sp.trigsimp(m04_unsimplified[1, 1].simplify()), (m04_unsimplified[1, 2].simplify()), sp.trigsimp(m04_unsimplified[1, 3].simplify())],
            [sp.trigsimp(m04_unsimplified[2, 0].simplify()), m04_unsimplified[2, 1].simplify(), sp.trigsimp(m04_unsimplified[2, 2].simplify()), sp.trigsimp(m04_unsimplified[2, 3].simplify())],
            [m04_unsimplified[3, 0].simplify(), m04_unsimplified[3, 1].simplify(), m04_unsimplified[3, 2].simplify(), m04_unsimplified[3, 3].simplify()]
        ])

    def _substitute_robot_params(self):
        self.mbee = self.mbee_symbolic.subs({self.lc: 0.2, self.la: 0.26, self.lb: 0.1425, self.l4: 0.0981})

    def _connect_coppelia(self, port):
        sim.simxFinish(-1)
        clientID = sim.simxStart('127.0.0.1', port, True, True, 2000, 5)
        if clientID != -1:
            print(f"Conectado a CoppeliaSim en el puerto {port}")
        else:
            print(f"No se pudo conectar a CoppeliaSim en el puerto {port}")
        return clientID

    def _get_joint_handles(self):
        if self.clientID == -1:
            return
        _, self.joint1 = sim.simxGetObjectHandle(self.clientID, 'Joint1', sim.simx_opmode_blocking)
        _, self.joint2 = sim.simxGetObjectHandle(self.clientID, 'Joint2', sim.simx_opmode_blocking)
        _, self.joint3 = sim.simxGetObjectHandle(self.clientID, 'Joint3', sim.simx_opmode_blocking)
        _, self.joint4 = sim.simxGetObjectHandle(self.clientID, 'Joint4', sim.simx_opmode_blocking)
        print(f"Handles articulaciones: J1:{self.joint1}, J2:{self.joint2}, J3:{self.joint3}, J4:{self.joint4}")

    def _get_suction_cup_handle(self):
        if self.clientID == -1:
            return
        _, self.suction_pad_handle = sim.simxGetObjectHandle(self.clientID, 'suctionPad', sim.simx_opmode_blocking)
        print(f"Handle ventosa: {self.suction_pad_handle}")

    def _get_camera_handle(self):
        if self.clientID == -1:
            return
        _, self.sensor_handle = sim.simxGetObjectHandle(self.clientID, 'Vision_sensor', sim.simx_opmode_blocking)
        print(f"Handle cámara: {self.sensor_handle}")

    def _update_joint_angles_from_robot(self):
        if self.clientID == -1:
            return
        for joint_name in self.joint_angles.keys():
            joint_handle = getattr(self, joint_name, None)
            if joint_handle is None:
                print(f"No existe handle para {joint_name}")
                continue
            ret_code, angle_rad = sim.simxGetJointPosition(self.clientID, joint_handle, sim.simx_opmode_blocking)
            if ret_code == sim.simx_return_ok:
                self.joint_angles[joint_name] = angle_rad
            else:
                print(f"No se pudo leer el ángulo actual de {joint_name}, se asume 0")

    def move_joint_by_delta(self, joint_name, delta_degrees):
        if self.clientID == -1:
            print("No conectado a CoppeliaSim.")
            return

        joint_handle = getattr(self, joint_name, None)
        if joint_handle is None:
            print(f"Joint '{joint_name}' no reconocido.")
            return

        delta_rad = delta_degrees * np.pi / 180
        current_angle_rad = self.joint_angles.get(joint_name, 0)
        new_angle_rad = current_angle_rad + delta_rad

        sim.simxSetJointTargetPosition(self.clientID, joint_handle, new_angle_rad, sim.simx_opmode_oneshot)
        print(f"Moviendo '{joint_name}' de {current_angle_rad * 180 / np.pi:.2f}° a {new_angle_rad * 180 / np.pi:.2f}°")

        self.joint_angles[joint_name] = new_angle_rad

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

            angulo_joint1 = th1_sol * 180 / np.pi
            angulo_joint2 = th2_sol * 180 / np.pi
            angulo_joint4 = rotacion

            self.move_joint_by_delta('joint1', angulo_joint1)
            self.move_joint_by_delta('joint2', angulo_joint2)
            self.move_joint_by_delta('joint4', -(angulo_joint1 + angulo_joint2)+angulo_joint4)  # Ajustar joint4 para mantener equilibrio

            print(f"✔️ Movimiento exitoso a XY ({px:.3f}, {py:.3f}).")
            print(f"Ángulos (rad): θ1={th1_sol.evalf():.3f}, θ2={th2_sol.evalf():.3f}, θ4={yaw:.3f}")

        except Exception as e:
            print("❌ Error al resolver cinemática inversa en XY:", e)

        
    def disconnect(self):
        if self.clientID != -1:
            sim.simxFinish(self.clientID)
            print("Desconectado de CoppeliaSim.")
            self.clientID = -1

    def obtener_foto(self):
        if self.clientID == -1:
            print("No conectado a CoppeliaSim.")
            return

        retCode, resolution, image=sim.simxGetVisionSensorImage(self.clientID,self.sensor_handle,0,sim.simx_opmode_oneshot_wait)
        img=np.array(image).astype(np.uint8)
        img.resize([resolution[1],resolution[0],3])
        img = np.flipud(img)
        
        return img
    
    def coger_ficha(self):
        self.move_joint_by_delta('joint3', -5)
        time.sleep(2)
        # Activar la ventosa
        res,retInts,retFloats,retStrings,retBuffer=sim.simxCallScriptFunction(self.clientID,'suctionPad', sim.sim_scripttype_childscript, 'setEffector', [1], [], [], '', sim.simx_opmode_blocking)

        time.sleep(1)
        self.move_joint_by_delta('joint3', 5)
        time.sleep(2)

    def soltar_ficha(self):
        self.move_joint_by_delta('joint3', -5)
        time.sleep(2)
        # Activar la ventosa
        res,retInts,retFloats,retStrings,retBuffer=sim.simxCallScriptFunction(self.clientID,'suctionPad', sim.sim_scripttype_childscript, 'setEffector', [0], [], [], '', sim.simx_opmode_blocking)

        time.sleep(1)
        self.move_joint_by_delta('joint3', 5)
        time.sleep(2)

    def move_posicion_inicial(self):
        """
        Mueve el robot a una posición para tomar una foto inicial.
        """
        # Calculamos el angulo necesario para que joint1 y joint2 estén en posicion inicial
        angulo_joint1 = 90 - self.joint_angles['joint1']* 180 / np.pi
        angulo_joint2 = -self.joint_angles['joint2']* 180 / np.pi

        print(f"Moviendo a posición inicial: Joint1: {angulo_joint1}°, Joint2: {angulo_joint2}°")
        self.move_joint_by_delta('joint1', angulo_joint1)
        self.move_joint_by_delta('joint2', angulo_joint2)
        self.move_joint_by_delta('joint4', -(angulo_joint1+angulo_joint2))
        time.sleep(2)

    def move_posicion_recta(self):
        """
        Mueve el robot a una posición recta
        """
        # Calculamos el angulo necesario para que joint1 y joint2 estén en una posición segura
        angulo_joint1 = -self.joint_angles['joint1']* 180 / np.pi
        angulo_joint2 = -self.joint_angles['joint2']* 180 / np.pi

        self.move_joint_by_delta('joint1', angulo_joint1)
        self.move_joint_by_delta('joint2', angulo_joint2)
        self.move_joint_by_delta('joint4', -(angulo_joint1+angulo_joint2))  # Bajar un poco para evitar colisiones
        time.sleep(2)

def pixel_to_world_linear(u, v,
                           img_resolution=(640, 480),
                           x_limits=(0.475, 0.025),     # ← eje real X, controlado por v
                           y_limits=(0.30, -0.30)):     # ← eje real Y, controlado por u
    width, height = img_resolution

    # Normalización de píxel a [0, 1]
    u_norm = u / width   # ← controla Y
    v_norm = v / height  # ← controla X

    # Interpolación con ejes cruzados
    x_world = x_limits[0] + v_norm * (x_limits[1] - x_limits[0])
    y_world = y_limits[0] + u_norm * (y_limits[1] - y_limits[0])

    return x_world, y_world