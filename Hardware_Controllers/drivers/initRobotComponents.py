import os
import sys
import json
import time
import RPi.GPIO as GPIO # Necessari per a la configuració GPIO del GestorInstancies

# Importa el GestorInstancies
from GestorInstancies import GestorInstancies

# Importa les classes dels controladors i gestors
from .controladors.Camera import Camera
from .controladors.Microphone import Microphone
from .controladors.Altaveu import Altaveu
# IMPORTANT: Hem d'assegurar que FileManager pugui rebre les instàncies en el seu constructor
from .FileManager import FileManager

from .controladors.MotorPasAPasNoNormalitzat import MotorPasAPas
from .controladors.Servomotor import Servomotor
from .controladors.Electroiman import Electroiman
from .ScaraController import ScaraController

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

def init_robot_components(gestor_instancies: GestorInstancies, config_data: dict) -> dict:
    """
    Inicialitza tots els components del robot basant-se en la configuració proporcionada
    i els registra al GestorInstancies.

    :param gestor_instancies: La instància del GestorInstancies (Singleton).
    :param config_data: El diccionari de configuració carregat del JSON.
    :return: Un diccionari amb les instàncies dels components accessibles (ex: {'camara': obj, 'motor_base': obj}).
    """
    print("\n--- Iniciant la Creació i Configuració dels Components ---")
    
    # Per guardar les instàncies que seran retornades per facilitar l'accés
    components_inicialitzats = {}

    # --- Configuració del mode GPIO globalment a través del GestorInstancies ---
    print("\n--- Configuració del mode GPIO globalment ---")
    gpio_settings = config_data.get("gpio_settings", {})
    if gpio_settings and "mode" in gpio_settings:
        gpio_mode_str = gpio_settings.get("mode")
        gestor_instancies.configurar_gpio_mode(gpio_mode_str)
    else:
        print("Avís: No s'ha trobat la configuració 'gpio_settings' o 'mode' al JSON. Saltant configuració GPIO.")

    # --- Càmera ---
    print("\n--- Creant i configurant la instància de la Camara ---")
    camera_config = config_data.get("camera", {})
    ins_camara = None
    if not camera_config:
        print("Avís: La configuració de la càmera no s'ha trobat al JSON o està buida.")
    else:
        ins_camara = gestor_instancies.crear_i_entrar_instancia(
            camera_config.get("nom"),
            Camera,
            nom_camera=camera_config.get("nom"),
            resolucio=tuple(camera_config.get("resolucio", (640, 480))),
            default_extension=camera_config.get("default_extension", "jpg"),
            default_metadata=camera_config.get("default_metadata", {}),
            mode_preview=camera_config.get("mode_preview", False)
        )
        if ins_camara:
            components_inicialitzats["camera"] = ins_camara
            print("Instància de la càmera creada i configurada.")
        else:
            print("ERROR: No s'ha pogut inicialitzar la càmera.")

    # --- Micròfon ---
    print("\n--- Creant i configurant la instància del Microphone ---")
    microphone_config = config_data.get("microphone", {})
    ins_microphone = None
    if not microphone_config:
        print("Avís: La configuració del micròfon no s'ha trobat al JSON o està buida.")
    else:
        ins_microphone = gestor_instancies.crear_i_entrar_instancia(
            microphone_config.get("nom"),
            Microphone,
            nom_microfon=microphone_config.get("nom"),
            samplerate=microphone_config.get("samplerate", 44100),
            channels=microphone_config.get("channels", 1),
            device_index=microphone_config.get("device_index"),
            dtype_gravacio=microphone_config.get("dtype_gravacio", "int16"),
            default_extension=microphone_config.get("default_extension", "wav"),
            default_metadata=microphone_config.get("default_metadata", {})
        )
        if ins_microphone:
            components_inicialitzats["microphone"] = ins_microphone
            print("Instància del micròfon creada i configurada.")
        else:
            print("ERROR: No s'ha pogut inicialitzar el micròfon.")

    # --- Altaveu ---
    print("\n--- Creant i configurant la instància de l'Altaveu ---")
    altaveu_config = config_data.get("altaveu", {})
    ins_altaveu = None
    if not altaveu_config:
        print("Avís: La configuració de l'altaveu no s'ha trobat al JSON o està buida.")
    else:
        ins_altaveu = gestor_instancies.crear_i_entrar_instancia(
            altaveu_config.get("nom"),
            Altaveu,
            nom_altaveu=altaveu_config.get("nom"),
            device_label_alsa=altaveu_config.get("device_label_alsa")
        )
        if ins_altaveu:
            components_inicialitzats["altaveu"] = ins_altaveu
            print("Instància de l'altaveu creada i configurada.")
        else:
            print("ERROR: No s'ha pogut inicialitzar l'altaveu.")

    # --- Motors Pas a Pas ---
    print("\n--- Creant i configurant les instàncies dels Motors Pas a Pas ---")
    motors_pas_a_pas_config = config_data.get("motors_pas_a_pas", [])
    motor_base = None
    motor_articulacio_secundaria = None
    motor_eix_z = None

    for motor_config in motors_pas_a_pas_config:
        motor_id = motor_config.get("nom")
        if motor_id:
            ins_motor_pas_a_pas = gestor_instancies.crear_i_entrar_instancia(
                motor_id,
                MotorPasAPas,
                nom=motor_config.get("nom"),
                pins_in=motor_config.get("pins_in"),
                passos_per_volta_motor=motor_config.get("passos_per_volta_motor"),
                reduccio_engranatge=motor_config.get("reduccio_engranatge"),
                mode_passos=motor_config.get("mode_passos")
            )
            if ins_motor_pas_a_pas:
                try:
                    ins_motor_pas_a_pas.setup_gpio()
                    ins_motor_pas_a_pas.calibrar()
                    components_inicialitzats[motor_id] = ins_motor_pas_a_pas
                    print(f"Instància de MotorPasAPas '{motor_id}' creada i configurada.")

                    # Assignar a les variables específiques per a ScaraController
                    if motor_id == "motor_base":
                        motor_base = ins_motor_pas_a_pas
                    elif motor_id == "motor_articulacio_secundaria":
                        motor_articulacio_secundaria = ins_motor_pas_a_pas
                    elif motor_id == "motor_eix_z":
                        motor_eix_z = ins_motor_pas_a_pas

                except Exception as e:
                    print(f"ERROR: No s'ha pogut configurar o calibrar el MotorPasAPas '{motor_id}': {e}")
            else:
                print(f"ERROR: No s'ha pogut inicialitzar el MotorPasAPas '{motor_id}'.")
        else:
            print("Avís: Configuració de MotorPasAPas sense 'id' al JSON. Saltant.")

    # --- Servomotor ---
    print("\n--- Creant i configurant la instància de Servomotor ---")
    servomotor_config = config_data.get("servomotor", {})
    ins_servomotor = None
    if not servomotor_config:
        print("Avís: La configuració de Servomotor no s'ha trobat al JSON o està buida.")
    else:
        ins_servomotor = gestor_instancies.crear_i_entrar_instancia(
            servomotor_config.get("nom"),
            Servomotor,
            nom_servomotor=servomotor_config.get("nom"),
            pin_gpio=servomotor_config.get("pin_gpio"),
            pwm_frequency=servomotor_config.get("pwm_frequency"),
            duty_cycle_min=servomotor_config.get("duty_cycle_min"),
            duty_cycle_max=servomotor_config.get("duty_cycle_max"),
            angle_min_operational=servomotor_config.get("angle_min_operational"),
            angle_max_operational=servomotor_config.get("angle_max_operational"),
            angle_validation_min=servomotor_config.get("angle_validation_min"),
            angle_validation_max=servomotor_config.get("angle_validation_max"),
            duty_cycle_validation_min=servomotor_config.get("duty_cycle_validation_min"),
            duty_cycle_validation_max=servomotor_config.get("duty_cycle_validation_max")
        )
        if ins_servomotor:
            components_inicialitzats["servomotor"] = ins_servomotor
            print("Instància de Servomotor creada i configurada.")
        else:
            print("ERROR: No s'ha pogut inicialitzar Servomotor.")
            
    # --- Electroiman ---
    print("\n--- Creant i configurant la instància de Electroiman ---")
    electroiman_config = config_data.get("electroiman", {})
    ins_electroiman = None
    if not electroiman_config:
        print("Avís: La configuració de Electroiman no s'ha trobat al JSON o està buida.")
    else:
        ins_electroiman = gestor_instancies.crear_i_entrar_instancia(
            electroiman_config.get("nom"),
            Electroiman,
            pin_control=electroiman_config.get("pin_control")
        )
        if ins_electroiman:
            try:
                ins_electroiman.setup()
                components_inicialitzats["electroiman"] = ins_electroiman
                print("Instància de Electroiman creada i configurada.")
            except Exception as e:
                print(f"ERROR: No s'ha pogut configurar l'Electroiman: {e}")
        else:
            print("ERROR: No s'ha pogut inicialitzar Electroiman.")

    # --- FileManager ---
    # Ara el FileManager rebrà les instàncies dels controladors directament.
    print("\n--- Creant i configurant la instància de FileManager ---")
    file_manager_config = config_data.get("file_manager", {})
    file_manager_instance = None
    if not file_manager_config:
        print("Avís: La configuració de FileManager no s'ha trobat al JSON o està buida.")
    else:
        try:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = find_project_root(current_script_dir)
            base_directory_path = os.path.join(project_root, file_manager_config.get("base_directory", "data"))
        except FileNotFoundError:
            print("Avís: No s'ha trobat l'arrel del projecte per a FileManager. Utilitzant directori base per defecte.")
            base_directory_path = file_manager_config.get("base_directory", "data")

        # Passem les instàncies als constructors del FileManager
        file_manager_instance = gestor_instancies.crear_i_entrar_instancia(
            file_manager_config.get("nom"),
            FileManager,
            base_directory=base_directory_path,
            default_prefix=file_manager_config.get("default_prefix", "robot_capture_"),
            scripts_folder_name=file_manager_config.get("scripts_folder_name", "scripts"),
            data_folder_name=file_manager_config.get("data_folder_name", "dades")
        )
        if file_manager_instance:
            components_inicialitzats["file_manager"] = file_manager_instance
            print("Instància de FileManager creada i configurada amb controladors.")
        else:
            print("ERROR: No s'ha pogut inicialitzar FileManager.")


        # --- Registre dels components amb FileManager ---
        print("\n--- Registrant instàncies de maquinari amb FileManager ---")
        

        if ins_camara:
            file_manager_instance.register_camera(ins_camara)
        if ins_microphone:
            file_manager_instance.register_microphone(ins_microphone)
        if ins_altaveu:
            file_manager_instance.register_speaker(ins_altaveu)
        print("Registre de components amb FileManager completat.")

    # --- ScaraController ---
    print("\n--- Creant i configurant la instància de ScaraController ---")
    scara_controller_config = config_data.get("scara_controller", {})
    if not scara_controller_config:
        print("Avís: La configuració de ScaraController no s'ha trobat al JSON o està buida.")
    else:
        # Obtenim les instàncies dels motors ja inicialitzats del gestor
        # Verifiquem que tots els components essencials per a ScaraController existeixin
        if not all([motor_base, motor_articulacio_secundaria, motor_eix_z, ins_servomotor, ins_electroiman]):
            print("ERROR: Un o més components essencials per a ScaraController no estan inicialitzats o no s'han trobat.")
            print(f"Estat: Base={bool(motor_base)}, ArticulacióSecundària={bool(motor_articulacio_secundaria)}, EixZ={bool(motor_eix_z)}, Servomotor={bool(ins_servomotor)}, Electroimant={bool(ins_electroiman)}")
        else:
            ins_scara_controller = gestor_instancies.crear_i_entrar_instancia(
                scara_controller_config.get("nom"),
                ScaraController,
                motor_base=motor_base,
                motor_articulacio_secundaria=motor_articulacio_secundaria,
                motor_eix_z=motor_eix_z,
                servomotor_canell=ins_servomotor,
                electroiman=ins_electroiman,
                config=scara_controller_config.get("config")
            )
            if ins_scara_controller:
                components_inicialitzats["scara_controller"] = ins_scara_controller
                print("Instància de ScaraController creada i configurada.")
            else:
                print("ERROR: No s'ha pogut inicialitzar ScaraController.")
    
    print("\n--- Finalitzada la Creació i Configuració dels Components ---")
    return components_inicialitzats