# --- Aquest codi aniria al teu fitxer principal (p.ex., main.py) ---
# Importa la teva classe ScaraController i les classes de motor/electroimant
# from scara_controller import ScaraController, MotorPasAPas, Servomotor, Electroiman

if __name__ == "__main__":
    # Defineix els pins GPIO per als teus motors i electroimant
    PINS_MOTOR_BASE = [17, 18, 27, 22]
    PINS_MOTOR_ARTICULACIO = [5, 6, 13, 19]
    PINS_MOTOR_Z = [26, 16, 20, 21]
    PIN_SERVOMOTOR_CANELL = 12
    PIN_ELECTROIMAN = 25

    # Defineix la configuració completa per a cada eix
    # AJUSTA AQUESTS VALORS ALS LÍMITS REALS, VELOCITATS DESITJADES I RELACIONS DE REDUCCIÓ DEL TEU ROBOT.
    ROBOT_CONFIG = {
        "base": {
            "limits": (-90.0, 90.0), # Graus físics de l'ARTICULACIÓ de la base
            "speeds": [120.0, 60.0, 30.0], # Velocitats en graus/segon de l'ARTICULACIÓ (ràpida, normal, lenta)
            "offset": 0.0, # L'angle de l'articulació que correspon a la posició 0 física del motor després de calibrar
            "reduction_ratio": 1.0 # Relació entre graus de l'articulació / graus del motor (ex: 2.0 si el motor gira el doble per 1 grau de l'articulació)
        },
        "articulacio_secundaria": {
            "limits": (0.0, 180.0),
            "speeds": [120.0, 60.0, 30.0],
            "offset": 0.0,
            "reduction_ratio": 1.0
        },
        "eix_z": {
            "limits": (-50.0, 50.0), # Podrien ser mm d'una translació vertical o graus d'un mecanisme rotatiu. Aquí, graus de l'articulació.
            "speeds": [90.0, 45.0, 20.0], # Velocitats de l'eix Z en graus/segon. 20.0 seria la més lenta (-1).
            "offset": 0.0,
            "reduction_ratio": 1.0
        },
        "canell": {
            "limits": (0.0, 180.0), # Límits operacionals del servomotor
            "speeds": [0.3, 0.5, 0.8], # Delays en segons per al servomotor (el més ràpid és el delay més petit). 0.8s seria el més lent (-1).
            "offset": 90.0, # Posició inicial del canell (p.ex., al centre)
            "reduction_ratio": 1.0 # El servomotor generalment controla l'articulació directament.
        }
    }

    # Crear instàncies dels motors i electroimant DINS de blocs 'with'
    with MotorPasAPas("Base", PINS_MOTOR_BASE) as motor_base, \
         MotorPasAPas("Articulació", PINS_MOTOR_ARTICULACIO) as motor_articulacio, \
         MotorPasAPas("EixZ", PINS_MOTOR_Z) as motor_z, \
         Servomotor(
            "Canell", PIN_SERVOMOTOR_CANELL,
            angle_min_operational=ROBOT_CONFIG["canell"]["limits"][0],
            angle_max_operational=ROBOT_CONFIG["canell"]["limits"][1]
         ) as servomotor_canell, \
         Electroiman(PIN_ELECTROIMAN) as electroiman:
        
        # Crear l'instància del controlador SCARA
        robot = ScaraController(
            motor_base=motor_base,
            motor_articulacio_secundaria=motor_articulacio,
            motor_eix_z=motor_z,
            servomotor_canell=servomotor_canell,
            electroiman=electroiman,
            config=ROBOT_CONFIG
        )

        try:
            # Calibrar el robot a les seves posicions inicials/offsets
            robot.calibrar_robot()
            time.sleep(1) # Donar temps a que els motors s'aturin

            # Moure el robot a una posició inicial segura amb velocitat per defecte (índex -2)
            print("\nMovent a una posició inicial segura (Ex: Base 0, Articulació 90, Z 0, Canell 90) amb velocitat per defecte...")
            robot.mou_a_posicio_eixos(0, 90, 0, 90) # No cal especificar speed_index, per defecte és -2
            time.sleep(2)

            # Exemple: Moure només l'eix de la Base a 45 graus a la velocitat més lenta (índex -1)
            print("\nMovent només l'eix de la Base a 45 graus (velocitat més lenta)...")
            robot.moure_sol_eix(ScaraController.EIX_BASE, 45, velocitat_index=-1)
            time.sleep(2)

            # Exemple: Moure només l'eix Z a -20 graus a la velocitat més ràpida (índex 0)
            print("\nMovent només l'eix Z a -20 graus (velocitat més ràpida)...")
            robot.moure_sol_eix(ScaraController.EIX_Z, -20, velocitat_index=0)
            time.sleep(2)

            # Exemple de tasca complexa: Agafar un objecte
            posicio_objecte_pickup = (45, 120, -10, 60) # Angles de l'articulació (Base, Articulació, Z, Canell)
            altura_seguretat_per_tasca = 30.0     # Angle Z de l'articulació per damunt de l'objecte

            print("\nRealitzant tasca d'AGAFAR objecte amb la velocitat de desplaçament per defecte (-2)...")
            robot.gestionar_objecte(
                posicio_objecte_pickup,
                altura_seguretat_per_tasca,
                agafar_objecte=True # Li diem que volem AGARFAR
            )
            time.sleep(2)

            # Exemple de tasca complexa: Deixar un objecte
            posicio_objecte_dropoff = (-45, 60, -20, 120)
            print("\nRealitzant tasca de DEIXAR objecte amb la velocitat de desplaçament per defecte (-2)...")
            robot.gestionar_objecte(
                posicio_objecte_dropoff,
                altura_seguretat_per_tasca,
                agafar_objecte=False # Li diem que volem DEIXAR
            )
            time.sleep(2)

            # Tornar a la posició inicial amb la velocitat "normal" (índex 1)
            print("\nTornant a la posició inicial amb velocitat 'normal'...")
            robot.mou_a_posicio_eixos(0, 90, 0, 90, velocitat_index=1)
            time.sleep(2)

        except Exception as e:
            print(f"\n!!!! Una excepció ha ocorregut durant l'execució del robot: {e}")
            robot.aturada_emergencia()
        finally:
            print("\nPrograma finalitzat. Els GPIOs seran netejats automàticament pels context managers.")
