import RPi.GPIO as GPIO
import time

class Servomotor:
    """
    Classe per controlar un servomotor connectat a un pin GPIO del Raspberry Pi.

    Aquesta classe està dissenyada per ser altament flexible i adaptable a qualsevol
    servomotor, ja que TOTS els seus paràmetres de calibració i límits de validació
    són configurables en el moment de crear la instància de la classe (al fer __init__).
    La configuració es fa una única vegada durant la instanciació de l'objecte,
    assumint que aquests paràmetres no canviaran durant l'execució normal del programa.

    Metàfora per entendre els paràmetres:
    Imagina que el teu servomotor és un COTXE i el senyal PWM és la CARRETERA.

    1.  Límits de la CARRETERA (Validació Absoluta):
        * `angle_validation_min`, `angle_validation_max`: Són com les "barreres de seguretat"
            de la carretera dels angles. Representen els límits físics/teòrics més enllà dels
            quals un angle no té sentit per a un servomotor (normalment 0° a 180°).
            Això assegura que no es demanin angles absurds.
        * `duty_cycle_validation_min`, `duty_cycle_validation_max`: Són les "barreres de seguretat"
            de la carretera del senyal PWM. Representen els límits del que el sistema PWM pot
            generar (normalment 0% a 100%).

    2.  Tram Útil de la Carretera per al teu COTXE (Calibració del Servomotor):
        * `duty_cycle_min`, `duty_cycle_max`: Aquests són com el "tram de la carretera" que el
            TEU cotxe (servo) sap utilitzar. Indiquen quin percentatge de cicle de treball
            (Duty Cycle) mou el teu servo específic als seus extrems.
            Ex: El teu servo concret pot moure's de 0° a 180° amb un 2.5% i 12.5% de DC.
            Un altre servo podria necessitar un 3.0% i un 11.0%. Aquests són els valors de calibració.

    3.  Ruta que vols que faci el teu COTXE (Rang Operatiu de l'Aplicació):
        * `angle_min_operational`, `angle_max_operational`: Són la "ruta" que tu vols que el
            TEU cotxe (servo) faci. Potser el teu servo pot fer 0°-180°, però en la teva aplicació
            (e.g., un braç robòtic), només vols que es mogui entre 45° i 135° per evitar col·lisions.
            Això s'usa per mapejar els angles desitjats a un rang de moviment segur i útil.

    La classe utilitza el protocol de gestió de context (`with ... as ...`) per assegurar
    una neteja segura dels pins GPIO un cop finalitzat el seu ús.
    """

    def __init__(self, nom_servomotor: str, pin_gpio: int,
                 pwm_frequency: int = 50,
                 # Paràmetres de calibració del cicle de treball per a aquest servomotor específic
                 # Representen el "tram útil de la carretera" per al teu servo.
                 duty_cycle_min: float = 2.5, duty_cycle_max: float = 12.5,
                 # Paràmetres del rang d'angles operatiu per a aquesta aplicació / muntatge
                 # Representen la "ruta que vols que faci el teu cotxe".
                 angle_min_operational: float = 0.0, angle_max_operational: float = 180.0,
                 # Límits ABSOLUTS de validació de la carretera dels angles (per si el sistema és no convencional)
                 # Són les "barreres de seguretat" de la carretera d'angles.
                 angle_validation_min: float = 0.0, angle_validation_max: float = 180.0,
                 # Límits ABSOLUTS de validació del cicle de treball (per si el sistema PWM és no convencional)
                 # Són les "barreres de seguretat" de la carretera del senyal PWM.
                 duty_cycle_validation_min: float = 0.0, duty_cycle_validation_max: float = 100.0):
        """
        Inicialitza la classe Servomotor amb tots els seus paràmetres configurables.

        Args:
            nom_servomotor (str): Nom identificatiu per al servomotor.
            pin_gpio (int): El número del pin GPIO BCM al qual està connectat el servomotor.
            pwm_frequency (int): Freqüència del PWM en Hz (per defecte 50 Hz, típic per la majoria de servos RC).
            
            duty_cycle_min (float): Cicle de treball mínim (%) que mou el servo al seu angle MÍNIM operatiu.
                                     (Ex: 2.5% per a 0 graus en molts servos).
            duty_cycle_max (float): Cicle de treball màxim (%) que mou el servo al seu angle MÀXIM operatiu.
                                     (Ex: 12.5% per a 180 graus en molts servos).
            
            angle_min_operational (float): L'angle mínim lògic/operatiu que el servomotor pot assolir en la teva aplicació.
                                            (Ex: 0.0 graus, o 30.0 si un braç mecànic xoca per sota).
            angle_max_operational (float): L'angle màxim lògic/operatiu que el servomotor pot assolir en la teva aplicació.
                                            (Ex: 180.0 graus, o 150.0 si un braç mecànic xoca per dalt).

            angle_validation_min (float): El límit inferior ABSOLUT per a qualsevol angle (per a validació general).
                                          (Per defecte 0.0 graus, ja que els servos RC generalment no van per sota).
            angle_validation_max (float): El límit superior ABSOLUT per a qualsevol angle (per a validació general).
                                          (Per defecte 180.0 graus, típic màxim per a servos RC).
            duty_cycle_validation_min (float): El límit inferior ABSOLUT per al duty cycle (per a validació general).
                                               (Per defecte 0.0%, un DC no pot ser negatiu).
            duty_cycle_validation_max (float): El límit superior ABSOLUT per al duty cycle (per a validació general).
                                               (Per defecte 100.0%, un DC no pot superar el 100%).
        """
        self.nom = nom_servomotor
        self._pin_gpio = pin_gpio
        
        # Assignació dels paràmetres a variables d'instància
        self._pwm_frequency = pwm_frequency
        self._duty_cycle_min = duty_cycle_min
        self._duty_cycle_max = duty_cycle_max
        self._angle_min_operational = angle_min_operational
        self._angle_max_operational = angle_max_operational

        self._angle_validation_min = angle_validation_min
        self._angle_validation_max = angle_validation_max
        self._duty_cycle_validation_min = duty_cycle_validation_min
        self._duty_cycle_validation_max = duty_cycle_validation_max

        self._pwm = None
        self._initialized = False

        # Realitzem les validacions de tots els paràmetres proporcionats
        self._validate_all_parameters()

        print(f"[{self.nom}]: Servomotor '{self.nom}' inicialitzat al pin GPIO {self._pin_gpio}.")
        print(f"[{self.nom}]: PWM Freq: {self._pwm_frequency}Hz, DC Operacional: [{self._duty_cycle_min}%, {self._duty_cycle_max}%].")
        print(f"[{self.nom}]: Angle Operacional: [{self._angle_min_operational}°, {self._angle_max_operational}°].")
        print(f"[{self.nom}]: Límits de Validació d'Angle: [{self._angle_validation_min}°, {self._angle_validation_max}°].")
        print(f"[{self.nom}]: Límits de Validació de DC: [{self._duty_cycle_validation_min}%, {self._duty_cycle_validation_max}%].")
        print(f"[{self.nom}]: **Recorda utilitzar 'with Servomotor(...) as servo:' per a una operació segura.**")

    def __enter__(self):
        """
        Mètode que es crida quan s'entra al bloc 'with'.
        Configura el mode GPIO i inicia el PWM.
        """
        print(f"[{self.nom}]: Entrant al context. Configuració de GPIO per al pin {self._pin_gpio}...")
        try:
            GPIO.setmode(GPIO.BCM) 
            GPIO.setup(self._pin_gpio, GPIO.OUT)
            
            self._pwm = GPIO.PWM(self._pin_gpio, self._pwm_frequency)
            self._pwm.start(0) 
            self._initialized = True
            print(f"[{self.nom}]: PWM iniciat al pin {self._pin_gpio} amb {self._pwm_frequency}Hz.")
        except RuntimeError as e:
            print(f"[{self.nom} ERROR]: Error en inicialitzar GPIO/PWM: {e}")
            print(f"[{self.nom} ERROR]: Assegura't que el programa s'executa amb permisos de superusuari (sudo).")
            self._initialized = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Mètode que es crida quan se surt del bloc 'with'.
        Atura el PWM i neteja els pins GPIO.
        """
        print(f"[{self.nom}]: Sortint del context. Aturant PWM i netejant GPIO...")
        if self._initialized and self._pwm:
            self._pwm.stop() 
            print(f"[{self.nom}]: PWM aturat.")
        GPIO.cleanup(self._pin_gpio) 
        self._initialized = False
        print(f"[{self.nom}]: GPIO.cleanup() realitzat per al pin {self._pin_gpio}.")
        # return False per propagar l'excepció si n'hi ha.

    def __del__(self):
        """
        Mètode finalitzador, actua com a salvaguarda si l'objecte es destrueix
        sense usar el bloc 'with'. Es recomana encaridament l'ús de 'with'.
        """
        print(f"[{self.nom}]: Executant __del__ (salvaguarda).")
        if self._initialized and self._pwm:
            try:
                self._pwm.stop()
                print(f"[{self.nom}]: PWM aturat per __del__.")
            except Exception as e:
                print(f"[{self.nom} ERROR]: Error aturant PWM en __del__: {e}")
        self._initialized = False

    # --- Secció: Validació de Paràmetres ---
    def _validate_all_parameters(self):
        """
        Valida tots els paràmetres de configuració passats a l'inicialitzar la classe.
        Això inclou els rangs operacionals i els límits de validació,
        assegurant la coherència i la seguretat en la configuració del servo.
        """
        # 1. Validar la freqüència PWM
        if not self._pwm_frequency > 0:
            raise ValueError("La freqüència del PWM ha de ser un valor positiu i major que 0.")

        # 2. Validar els límits absoluts de validació (les "barreres de la carretera")
        if not (self._angle_validation_min <= self._angle_validation_max):
            raise ValueError(f"Els límits de validació d'angle són invàlids: min ({self._angle_validation_min}) ha de ser <= max ({self._angle_validation_max}).")
        if not (self._duty_cycle_validation_min <= self._duty_cycle_validation_max):
            raise ValueError(f"Els límits de validació del duty cycle són invàlids: min ({self._duty_cycle_validation_min}) ha de ser <= max ({self._duty_cycle_validation_max}).")
        
        # 3. Validar el rang d'angles operacionals ("la ruta del teu cotxe")
        # Ha d'estar dins dels límits absoluts i tenir un rang vàlid.
        if not (self._angle_validation_min <= self._angle_min_operational < self._angle_max_operational <= self._angle_validation_max):
            raise ValueError(
                f"El rang d'angles operacionals ({self._angle_min_operational}, {self._angle_max_operational}) "
                f"és invàlid o fora dels límits de validació absoluts "
                f"[{self._angle_validation_min}, {self._angle_validation_max}]."
                " angle_min_operational ha de ser estrictament menor que angle_max_operational."
            )

        # 4. Validar el rang de duty cycle operacionals ("el tram útil de la carretera")
        # Ha d'estar dins dels límits absoluts i tenir un rang vàlid.
        if not (self._duty_cycle_validation_min <= self._duty_cycle_min < self._duty_cycle_max <= self._duty_cycle_validation_max):
            # Nota: S'usa '<' per a duty_cycle_min amb el mínim de validació per assegurar que el duty cycle sigui
            # efectivament operatiu (major que 0%) i duty_cycle_min < duty_cycle_max.
            raise ValueError(
                f"El rang de cicles de treball operacionals ({self._duty_cycle_min}%, {self._duty_cycle_max}%) "
                f"és invàlid o fora dels límits de validació absoluts "
                f"[{self._duty_cycle_validation_min}%, {self._duty_cycle_validation_max}%]. "
                "duty_cycle_min ha de ser menor que duty_cycle_max i tots dos dins dels límits de validació."
            )
    
    def get_current_configuration(self) -> dict:
        """
        Retorna la configuració actual de la instància del servomotor,
        incloent tots els paràmetres de calibració i validació.
        """
        return {
            "nom": self.nom,
            "pin_gpio": self._pin_gpio,
            "pwm_frequency": self._pwm_frequency,
            "duty_cycle_min_operational": self._duty_cycle_min,
            "duty_cycle_max_operational": self._duty_cycle_max,
            "angle_min_operational": self._angle_min_operational,
            "angle_max_operational": self._angle_max_operational,
            "angle_validation_min": self._angle_validation_min,
            "angle_validation_max": self._angle_validation_max,
            "duty_cycle_validation_min": self._duty_cycle_validation_min,
            "duty_cycle_validation_max": self._duty_cycle_validation_max
        }

    # --- Secció: Funcionalitats de Moviment ---
    def _map_angle_to_duty_cycle(self, angle: float) -> float:
        """
        Converteix un angle en graus al cicle de treball (Duty Cycle) percentual corresponent.
        Aquest mètode utilitza el mapeig lineal basat en el rang d'angles operacionals
        i el rang de cicles de treball operacionals configurats per a aquesta instància.
        
        S'assegura que l'angle d'entrada es "fixa" (clamp) dins del rang operacional
        i que el cicle de treball resultant es "fixa" dins dels límits de validació absoluts.

        Args:
            angle (float): L'angle desitjat en graus.

        Returns:
            float: El cicle de treball corresponent (0-100%), ajustat als límits.
        """
        """
        # 1. Limitem l'angle d'entrada al rang OPERACIONAL definit per la instància
        # Això significa que si demanes 0° i el teu rang operacional és 30°-150°, l'angle s'interpreta com 30°.
        clamped_angle = max(self._angle_min_operational, min(self._angle_max_operational, angle))
        
        # 2. Calculem el cicle de treball utilitzant el mapeig lineal
        # Traduïm l'angle (dins el rang operacional) al seu cicle de treball corresponent (dins el rang de DC operacional).
        if self._angle_max_operational == self._angle_min_operational:
            duty_cycle = self._duty_cycle_min
        else:
            duty_cycle = self._duty_cycle_min + (clamped_angle - self._angle_min_operational) * \
                        (self._duty_cycle_max - self._duty_cycle_min) / (self._angle_max_operational - self._angle_min_operational)
        
        # 3. Assegurem que el duty cycle calculat estigui dins dels límits ABSOLUTS de validació.
        # Aquesta és una capa de seguretat final per si el mapeig generés un valor inesperat.
        return max(self._duty_cycle_validation_min, min(self._duty_cycle_validation_max, duty_cycle))
        """
        # ... (Part 1: clamp_angle - Sense canvis, això és correcte) ...
        clamped_angle = max(self._angle_min_operational, min(self._angle_max_operational, angle))

        # --- NOVA LÒGICA DE MAPATGGE ---

        # Defineix els límits absoluts d'angle del servo (normalment 0-180)
        # i els seus Duty Cycles de calibració (2.190% per 0°, 12.290% per 180°).
        absolute_angle_min = 0.0
        absolute_angle_max = 180.0
        
        # PAS 1: Calcular quin Duty Cycle (DC) correspon a l'angle_min_operational i angle_max_operational
        # Utilitzem la calibració global (duty_cycle_min/max per 0-180) per trobar aquests punts.

        # DC que correspon a angle_min_operational (per exemple, per a 45°)
        # Aquesta és la clau: Mapeja 45° de 0-180 a un Duty Cycle concret.
        if absolute_angle_max - absolute_angle_min == 0: # Evitar divisió per zero
            dc_at_operational_min = self._duty_cycle_min
        else:
            dc_at_operational_min = self._duty_cycle_min + \
                                    (self._angle_min_operational - absolute_angle_min) * \
                                    (self._duty_cycle_max - self._duty_cycle_min) / \
                                    (absolute_angle_max - absolute_angle_min)

        # DC que correspon a angle_max_operational (per exemple, per a 135°)
        # Mapeja 135° de 0-180 a un Duty Cycle concret.
        if absolute_angle_max - absolute_angle_min == 0: # Evitar divisió per zero
            dc_at_operational_max = self._duty_cycle_max
        else:
            dc_at_operational_max = self._duty_cycle_min + \
                                    (self._angle_max_operational - absolute_angle_min) * \
                                    (self._duty_cycle_max - self._duty_cycle_min) / \
                                    (absolute_angle_max - absolute_angle_min)

        # PAS 2: Ara que tenim els DC's per als límits operacionals (dc_at_operational_min i dc_at_operational_max),
        # mapegem l'angle real que volem (clamped_angle) dins del rang operacional,
        # al nou rang de Duty Cycles.

        operational_angle_span = self._angle_max_operational - self._angle_min_operational
        
        if operational_angle_span == 0: # Evitar divisió per zero
            duty_cycle = dc_at_operational_min
        else:
            # Calculem la posició proporcional de l'angle clamped dins del rang operacional (de 0 a 1).
            percentage_in_operational_range = (clamped_angle - self._angle_min_operational) / operational_angle_span
            
            # Apliquem aquest percentatge al nou rang de Duty Cycles.
            duty_cycle = dc_at_operational_min + \
                         percentage_in_operational_range * \
                         (dc_at_operational_max - dc_at_operational_min)

        # ... (Part 3: Validació final del Duty Cycle - Sense canvis, això és correcte) ...
        return max(self._duty_cycle_validation_min, min(self._duty_cycle_validation_max, duty_cycle))

    def move_to_angle(self, angle: float, delay: float = 0.5):
        """
        Mou el servomotor a un angle específic en graus.
        L'angle s'interpretarà dins del rang lògic/operacional configurat.

        Args:
            angle (float): L'angle desitjat en graus.
            delay (float): Temps d'espera en segons després del moviment per estabilitzar el servo.
        """
        if not self._initialized or self._pwm is None:
            print(f"[{self.nom} ERROR]: Servomotor no inicialitzat. Assegura't d'usar el bloc 'with' per iniciar-lo.")
            return

        duty_cycle = self._map_angle_to_duty_cycle(angle)
        
        print(f"[{self.nom}]: Movent a angle {angle}° (Duty Cycle calculat: {duty_cycle:.2f}%).")
        try:
            self._pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(delay)
        except Exception as e:
            print(f"[{self.nom} ERROR]: Error en moure el servomotor a l'angle {angle}°: {e}")

