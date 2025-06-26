from typing import Tuple, Dict, Any, List
import time
import threading
from .controladors.MotorPasAPasNoNormalitzat import MotorPasAPas
from .controladors.Servomotor import Servomotor
from .controladors.Electroiman import Electroiman

class ScaraController:
    """
    Controlador principal per a un robot SCARA, gestionant els seus eixos
    (3 motors pas a pas, 1 servomotor) i un electroimant.
    Opera amb angles de les articulacions i posicions relatives/absolutes.
    """

    # Identificadors d'eix per a més claredat
    EIX_BASE = 0
    EIX_ARTICULACIO_SECUNDARIA = 1
    EIX_Z = 2
    EIX_CANELL = 3

    def __init__(self,
                 motor_base: MotorPasAPas,
                 motor_articulacio_secundaria: MotorPasAPas,
                 motor_eix_z: MotorPasAPas,
                 servomotor_canell: Servomotor,
                 electroiman: Electroiman,
                 config: Dict[str, Dict[str, Any]]
                ):
        """
        Inicialitza el controlador SCARA amb les instàncies dels seus components
        i la configuració detallada de cada eix.

        Args:
            motor_base (MotorPasAPas): Motor de la base del robot (Eix 0).
            motor_articulacio_secundaria (MotorPasAPas): Motor de la segona articulació (Eix 1).
            motor_eix_z (MotorPasAPas): Motor de l'eix vertical (Eix 2).
            servomotor_canell (Servomotor): Servomotor per a la rotació del canell (Eix 3).
            electroiman (Electroiman): Electroimant per a la funció de pinça.
            config (Dict): Diccionari amb la configuració per a cada eix.
                            Exemple de format:
                            {
                                "base": {
                                    "limits": (-90.0, 90.0), # Graus de l'articulació (després de tots els reductors)
                                    "speeds": [120.0, 60.0, 30.0], # Graus/segon (de la més ràpida a la més lenta)
                                    "offset": 0.0, # Posició 0 lògica després de calibratge de l'articulació
                                    "reduction_ratio": 1.0 # Relació entre graus de l'articulació / graus del motor
                                },
                                "articulacio_secundaria": {
                                    "limits": (0.0, 180.0),
                                    "speeds": [120.0, 60.0, 30.0],
                                    "offset": 0.0,
                                    "reduction_ratio": 1.0
                                },
                                "eix_z": {
                                    "limits": (-50.0, 50.0),
                                    "speeds": [90.0, 45.0, 20.0],
                                    "offset": 0.0,
                                    "reduction_ratio": 1.0
                                },
                                "canell": {
                                    "limits": (0.0, 180.0),
                                    "speeds": [0.3, 0.5, 0.8], # Delay en segons (el més ràpid és el delay més petit)
                                    "offset": 90.0,
                                    "reduction_ratio": 1.0
                                }
                            }
        """
        self.motors = {
            self.EIX_BASE: motor_base,
            self.EIX_ARTICULACIO_SECUNDARIA: motor_articulacio_secundaria,
            self.EIX_Z: motor_eix_z,
            self.EIX_CANELL: servomotor_canell
        }
        self.electroiman = electroiman
        self.config = config

        # Inicialització de la posició actual de cada articulació
        self._current_angles = [
            self.config["base"]["offset"],
            self.config["articulacio_secundaria"]["offset"],
            self.config["eix_z"]["offset"],
            self.config["canell"]["offset"]
        ]
        
        self._validate_initial_config()

        print("ScaraController inicialitzat amb la configuració proporcionada.")
        self._print_current_angles()
        print("Preparat per rebre ordres.")


    def __enter__(self):
        """
        Mètode que es crida quan s'entra al bloc 'with'.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        S'executa quan es surt del bloc 'with', fins i tot si hi ha una exc>        """
        pass

    def _validate_initial_config(self):
        """Comprova que la configuració inicial conté tots els paràmetres necessaris."""
        required_keys = ["limits", "speeds", "offset", "reduction_ratio"]
        for axis_name in ["base", "articulacio_secundaria", "eix_z", "canell"]:
            if axis_name not in self.config:
                raise ValueError(f"Falta la configuració per a l'eix '{axis_name}'.")
            for key in required_keys:
                if key not in self.config[axis_name]:
                    raise ValueError(f"Falta la clau '{key}' a la configuració de l'eix '{axis_name}'.")
            if not isinstance(self.config[axis_name]["speeds"], list) or not self.config[axis_name]["speeds"]:
                raise ValueError(f"Les velocitats per a '{axis_name}' han de ser una llista no buida.")
            if not self.config[axis_name]["reduction_ratio"] > 0:
                raise ValueError(f"La relació de reducció per a '{axis_name}' ha de ser positiva.")


    def _get_axis_name(self, axis_id: int) -> str:
        """Retorna el nom de l'eix a partir del seu ID."""
        if axis_id == self.EIX_BASE: return "base"
        if axis_id == self.EIX_ARTICULACIO_SECUNDARIA: return "articulacio_secundaria"
        if axis_id == self.EIX_Z: return "eix_z"
        if axis_id == self.EIX_CANELL: return "canell"
        raise ValueError(f"ID d'eix desconegut: {axis_id}")

    def _print_current_angles(self):
        """Mètode auxiliar per imprimir les posicions angulars actuals."""
        print(f"Posició actual (graus de l'articulació):")
        print(f"  Base (Eix {self.EIX_BASE}): {self._current_angles[self.EIX_BASE]:.2f}°")
        print(f"  Articulació Secundària (Eix {self.EIX_ARTICULACIO_SECUNDARIA}): {self._current_angles[self.EIX_ARTICULACIO_SECUNDARIA]:.2f}°")
        print(f"  Eix Z (Eix {self.EIX_Z}): {self._current_angles[self.EIX_Z]:.2f}°")
        print(f"  Canell (Eix {self.EIX_CANELL}): {self._current_angles[self.EIX_CANELL]:.2f}°")

    def _validate_angle(self, axis_id: int, angle: float) -> bool:
        """
        Valida que un angle estigui dins dels límits definits per a una articulació.
        Args:
            axis_id (int): ID de l'eix (0, 1, 2, 3).
            angle (float): Angle de l'articulació a validar.
        Returns:
            bool: True si l'angle és vàlid, False en cas contrari.
        """
        axis_name = self._get_axis_name(axis_id)
        min_limit, max_limit = self.config[axis_name]["limits"]

        if not (min_limit <= angle <= max_limit):
            print(f"ADVERTÈNCIA: Angle {angle:.2f}° per a l'articulació '{axis_name}' (ID {axis_id}) fora de límits [{min_limit:.2f}°, {max_limit:.2f}°].")
            return False
        return True

    def _get_speed_value(self, axis_id: int, speed_index: int) -> float:
        """
        Obté el valor de velocitat (graus/s o delay) per a un índex de velocitat donat.
        Args:
            axis_id (int): ID de l'eix.
            speed_index (int): Índex de la velocitat (0 per la més ràpida, -1 per la més lenta, etc.).
        Returns:
            float: Valor de velocitat/delay.
        Raises:
            IndexError: Si l'índex de velocitat no és vàlid.
        """
        axis_name = self._get_axis_name(axis_id)
        speeds = self.config[axis_name]["speeds"]
        try:
            return speeds[speed_index]
        except IndexError:
            raise IndexError(f"Índex de velocitat {speed_index} fora de rang per a l'eix '{axis_name}'. Velocitats disponibles: {len(speeds)}.")

    # --- Mètodes de Moviment ---

    def moure_sol_eix(self, axis_id: int, target_angle: float, velocitat_index: int = -2) -> bool:
        """
        Mou un sol eix (articulació) del robot a una posició angular específica.

        Args:
            axis_id (int): L'ID de l'eix a moure (0: Base, 1: Articulació Secundària, 2: Eix Z, 3: Canell).
            target_angle (float): Angle objectiu per a l'articulació en graus.
            velocitat_index (int): Índex de la velocitat a utilitzar (0 per la més ràpida, -1 per la més lenta, etc.).

        Returns:
            bool: True si el moviment s'ha iniciat amb èxit, False en cas contrari.
        """
        axis_name = self._get_axis_name(axis_id)
        print(f"Iniciant moviment de l'eix '{axis_name}' (ID {axis_id}) a {target_angle:.2f}°...")

        # 1. Validar l'angle de l'articulació
        if not self._validate_angle(axis_id, target_angle):
            print(f"ERROR: Angle {target_angle:.2f}° per a l'eix '{axis_name}' fora de límits. Moviment cancel·lat.")
            return False

        # 2. Obtenir velocitat i calcular l'angle per al motor
        try:
            speed_value = self._get_speed_value(axis_id, velocitat_index)
        except IndexError as e:
            print(f"ERROR: {e}. Moviment de l'eix '{axis_name}' cancel·lat.")
            return False

        # Apply reduction ratio to convert articulation angle to motor angle
        reduction_ratio = self.config[axis_name]["reduction_ratio"]
        target_angle_for_motor = target_angle * reduction_ratio

        # 3. Moure el motor
        motor = self.motors[axis_id]
        if isinstance(motor, MotorPasAPas):
            motor.moure_a_graus(target_angle_for_motor, speed_value)
        elif isinstance(motor, Servomotor):
            motor.move_to_angle(target_angle_for_motor, speed_value)
        else:
            print(f"ERROR: Tipus de motor desconegut per a l'eix '{axis_name}'.")
            return False
        
        # 4. Actualitzar la posició angular interna del controlador DESPRÉS del moviment
        self._current_angles[axis_id] = target_angle
        print(f"Moviment de l'eix '{axis_name}' completat a {target_angle:.2f}°.")
        return True


    def mou_a_posicio_eixos(self,
                            graus_base: float,
                            graus_articulacio_secundaria: float,
                            graus_eix_z: float,
                            graus_canell: float,
                            velocitat_index: int = -2): # Default changed to -2 (antepenultimate)
        """
        Mou tots els eixos del robot a les posicions angulars especificades de l'articulació
        utilitzant fils (threads) per a un moviment concurrent.

        Args:
            graus_base (float): Angle objectiu per a la base (Articulació 0).
            graus_articulacio_secundaria (float): Angle objectiu per a l'articulació secundària (Articulació 1).
            graus_eix_z (float): Angle objectiu per a l'eix Z (Articulació 2).
            graus_canell (float): Angle objectiu per a la rotació del canell (Articulació 3).
            velocitat_index (int): Índex de la velocitat a utilitzar (0 per ràpida, 1 per normal, -1 per lenta, etc.).
        
        Returns:
            bool: True si tots els moviments s'han completat amb èxit, False en cas contrari.
        """
        target_angles = {
            self.EIX_BASE: graus_base,
            self.EIX_ARTICULACIO_SECUNDARIA: graus_articulacio_secundaria,
            self.EIX_Z: graus_eix_z,
            self.EIX_CANELL: graus_canell
        }

        print("\nIniciant moviment concurrent a nova posició d'eixos:")

        # 1. Validar tots els angles de les articulacions abans de moure qualsevol eix
        for axis_id, angle in target_angles.items():
            if not self._validate_angle(axis_id, angle):
                print("ERROR: Un o més angles estan fora de límits de l'articulació. Moviment concurrent cancel·lat.")
                return False

        # Create a list to hold our threads
        threads = []
        # A list to store the results of each thread (True/False for success)
        # Initialize with True, so any failure sets it to False
        results = [True] * len(self.motors) 

        # 2. Launch a thread for each axis movement using moure_sol_eix
        for i, (axis_id, target_angle) in enumerate(target_angles.items()):
            # Define a target function that will be executed by each thread
            def move_single_axis_thread_wrapper(axis_id_inner, target_angle_inner, velocitat_index_inner, result_list, index):
                success = self.moure_sol_eix(axis_id_inner, target_angle_inner, velocitat_index_inner)
                result_list[index] = success

            thread = threading.Thread(
                target=move_single_axis_thread_wrapper,
                args=(axis_id, target_angle, velocitat_index, results, i)
            )
            threads.append(thread)
            thread.start() # Start the thread

        # 3. Wait for all threads to complete
        for thread in threads:
            thread.join() # This blocks until the thread finishes

        # 4. Check if all movements were successful
        if all(results):
            print("Tots els moviments concurrents s'han completat amb èxit.")
            self._print_current_angles()
            return True
        else:
            print("ADVERTÈNCIA: Un o més moviments concurrents no s'han completat amb èxit.")
            self._print_current_angles()
            return False

    # --- Mètodes d'Operació de l'Electroimant ---
    def activar_pinça(self):
        """Activa l'electroimant per agafar un objecte."""
        print("\nActivant pinça (electroimant)...")
        if self.electroiman.activar():
            print("Pinça activada amb èxit.")
        else:
            print("No s'ha pogut activar la pinça.")

    def desactivar_pinça(self):
        """Desactiva l'electroimant per deixar anar un objecte."""
        print("\nDesactivant pinça (electroimant)...")
        if self.electroiman.desactivar():
            print("Pinça desactivada amb èxit.")
        else:
            print("No s'ha pogut desactivar la pinça.")

    # --- Mètodes de Seguretat / Manteniment ---
    def aturada_emergencia(self):
        """
        Atura tots els motors immediatament i desactiva l'electroimant.
        Aquesta és una aturada suau a nivell de programari.
        """
        print("\n*** ATURADA D'EMERGÈNCIA ACTIVADA! ***")
        for axis_id, motor in self.motors.items():
            if isinstance(motor, MotorPasAPas):
                motor.release_motor()
            elif isinstance(motor, Servomotor):
                motor.move_to_angle(90, delay=0.1) # Move to center (0-180 assumed)
        self.desactivar_pinça()
        print("*** TOTS ELS MOTORS I L'ELECTROIMANT ATURATS. ***")

    def calibrar_robot(self):
        """
        Calibra cada eix del robot movent-lo a una posició de referència
        i establint la posició actual de l'articulació a l'offset definit per l'eix.
        NOTA: Això és una simulació sense sensors de fi de carrera.
        """
        print("\nIniciant calibratge del robot...")

        for axis_id in [self.EIX_BASE, self.EIX_ARTICULACIO_SECUNDARIA, self.EIX_Z]:
            axis_name = self._get_axis_name(axis_id)
            print(f"Calibrant Eix {axis_id} ({axis_name})...")
            motor = self.motors[axis_id]
            if isinstance(motor, MotorPasAPas):
                # Assumim que el `calibrar` del MotorPasAPas porta l'eix de sortida del motor a 0 graus.
                motor.calibrar(direccio_calibratge=MotorPasAPas.DIRECCIO_ENRERE)
                # Ara, la posició de l'articulació s'estableix al seu offset.
                self._current_angles[axis_id] = self.config[axis_name]["offset"]
            else:
                print(f"ADVERTÈNCIA: L'eix {axis_id} no és un MotorPasAPas per al calibratge amb `calibrar()`.")

        print(f"Calibrant Eix {self.EIX_CANELL} (Canell)...")
        servo_canell = self.motors[self.EIX_CANELL]
        if isinstance(servo_canell, Servomotor):
            offset_canell = self.config["canell"]["offset"]
            # Per al calibratge, utilitzem una velocitat per defecte segura (p.ex., la més lenta)
            default_speed_index = -1 
            delay_canell = self.config["canell"]["speeds"][default_speed_index]
            servo_canell.move_to_angle(offset_canell, delay=delay_canell)
            self._current_angles[self.EIX_CANELL] = offset_canell
        else:
            print(f"ADVERTÈNCIA: L'eix {self.EIX_CANELL} no és un Servomotor.")

        print("Calibratge del robot SCARA completat. Posicions inicials de l'articulació establertes.")
        self._print_current_angles()

    # --- Funcions per a tasques complexes (Gestió d'objectes) ---

    def gestionar_objecte(self,
                          posicio_objecte: Tuple[float, float, float, float],
                          altura_seguretat_z: float,
                          agafar_objecte: bool, # True per agafar, False per deixar anar
                          velocitat_desplacament_index: int = -2):
        """
        Realitza la seqüència de moviments per agafar o deixar anar un objecte.

        Args:
            posicio_objecte (Tuple[float, float, float, float]): (Graus Base, Graus Articulació, Graus Z, Graus Canell)
                                                                 Posició exacta de l'objecte o destí.
                                                                 Aquests són angles de les articulacions.
            altura_seguretat_z (float): Una altura en l'eix Z (graus o unitats de l'eix Z de l'articulació)
                                       a la qual el robot es mou per sobre de l'objecte/destí abans de baixar,
                                       i després de pujar per evitar col·lisions.
            agafar_objecte (bool): Si és True, activa l'electroimant per agafar. Si és False, el desactiva per deixar anar.
            velocitat_desplacament_index (int): Índex de la velocitat a utilitzar per als moviments de desplaçament X/Y/Canell.
                                            Els moviments Z crítics utilitzaran la velocitat més lenta.
        """
        accio_str = "AGAFAR" if agafar_objecte else "DEIXAR"
        print(f"\nIniciant procés per {accio_str} objecte a {posicio_objecte}...")

        # Validar l'altura de seguretat Z
        if not self._validate_angle(self.EIX_Z, altura_seguretat_z):
            print(f"ERROR: Altura de seguretat Z ({altura_seguretat_z}) fora de límits. Cancel·lant {accio_str}.")
            return False

        # Velocitat més lenta per als moviments Z crítics
        velocitat_z_critica_index = -1 # Última velocitat de la llista (la més lenta)

        # 1. Anar a la posició X/Y/Rotació canell per sobre de l'objecte/destí, a una altura de seguretat
        print(f"Movent a posició de seguretat (Z de l'articulació: {altura_seguretat_z})...")
        if not self.mou_a_posicio_eixos(
            posicio_objecte[self.EIX_BASE],
            posicio_objecte[self.EIX_ARTICULACIO_SECUNDARIA],
            altura_seguretat_z, # Aquí només movem Z a l'altura de seguretat
            posicio_objecte[self.EIX_CANELL],
            velocitat_index=velocitat_desplacament_index # Velocitat normal per als desplaçaments
        ):
            print(f"ERROR: No s'ha pogut arribar a la posició de seguretat. Cancel·lant {accio_str}.")
            return False
        time.sleep(1) # Espera per estabilitzar

        # 2. Baixar a la posició exacta de l'objecte/destí (només moviment de l'eix Z)
        print(f"Baixant per {accio_str} l'objecte (Eix Z amb velocitat lenta)...")
        if not self.moure_sol_eix(
            self.EIX_Z,
            posicio_objecte[self.EIX_Z], # Angle Z objectiu
            velocitat_index=velocitat_z_critica_index # Velocitat més lenta
        ):
            print(f"ERROR: No s'ha pogut baixar a l'objecte/destí. Cancel·lant {accio_str}.")
            return False
        time.sleep(0.5) # Espera per estabilitzar

        # 3. Activar/Desactivar l'electroimant
        if agafar_objecte:
            self.activar_pinça()
        else:
            self.desactivar_pinça()
        time.sleep(1) # Donar temps a l'electroimant per actuar

        # 4. Pujar de nou a l'altura de seguretat (només moviment de l'eix Z)
        print(f"Pujant de nou a altura de seguretat (Z de l'articulació: {altura_seguretat_z}) amb velocitat lenta...")
        if not self.moure_sol_eix(
            self.EIX_Z,
            altura_seguretat_z, # Tornem a l'altura de seguretat
            velocitat_index=velocitat_z_critica_index # Velocitat més lenta
        ):
            print(f"ERROR: No s'ha pogut pujar amb/després de l'objecte. L'objecte pot no estar segur. Cancel·lant {accio_str}.")
            return False
        
        # Opcional: Si el moviment de pujada és crític, podem voler moure els altres eixos
        # en el mateix temps, però per a la petició actual només Z es mou.
        # En el teu cas, moure sol eix Z és el que volies.

        print(f"Procés de {accio_str} objecte completat amb èxit.")
        return True
