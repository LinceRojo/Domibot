import RPi.GPIO as GPIO
import time

# Assegura que GPIO.cleanup() es crida en sortir del programa,
# però això ho gestionarà el context manager i/o __del__ de la classe.
# atexit.register(GPIO.cleanup) # Podria ser problemàtic si s'usa amb diversos motors/dispositius GPIO

class MotorPasAPas:
    """
    Classe per controlar un motor pas a pas (Stepper Motor), especialment dissenyada
    per al 28BYJ-48 amb driver ULN2003 en una Raspberry Pi.
    """

    # Constants per a la direcció del moviment
    DIRECCIO_ENDAVANT = True
    DIRECCIO_ENRERE = False

    def __init__(self, nom: str, pins_in: list, passos_per_volta_motor: int = 32, reduccio_engranatge: float = 64.0, mode_passos: str = 'half'):
        """
        Inicialitza una nova instància de MotorPasAPas.

        Args:
            nom (str): Nom identificatiu del motor.
            pins_in (list): Llista de 4 pins GPIO (numeració BCM) connectats a IN1, IN2, IN3, IN4 del driver ULN2003.
            passos_per_volta_motor (int): Nombre de "passos complets" interns del motor abans de la reducció.
                                         Per al 28BYJ-48, sol ser 32.
            reduccio_engranatge (float): Relació de reducció de l'engranatge del motor (p.ex., 64.0 per 64:1).
                                         Per al 28BYJ-48, sol ser aproximadament 63.68395, però 64.0 és comú per simplicitat.
            mode_passos (str): Mode de funcionament dels passos ('full' o 'half').
                               El 28BYJ-48 normalment es fa servir en 'half' per més precisió i suavitat.
        """
        self._is_setup = False # Nou: Estat per saber si els pins estan configurats
        if not all(isinstance(pin, int) for pin in pins_in) or len(pins_in) != 4:
            raise ValueError("`pins_in` ha de ser una llista de 4 números de pin (BCM).")
        if mode_passos not in ['full', 'half']:
            raise ValueError("`mode_passos` ha de ser 'full' o 'half'.")
        if passos_per_volta_motor <= 0 or reduccio_engranatge <= 0:
            raise ValueError("`passos_per_volta_motor` i `reduccio_engranatge` han de ser valors positius.")

        self.nom = nom
        self.pins_in = pins_in
        self.passos_per_volta_motor = passos_per_volta_motor
        self.reduccio_engranatge = reduccio_engranatge
        self.mode_passos = mode_passos
        
        #self._is_setup = False # Nou: Estat per saber si els pins estan configurats
        self.num_pins_control = len(self.pins_in)

        if self.mode_passos == 'half':
            self.num_pasos_seq = self.num_pins_control * 2 # 8 passos per cicle (half step)
            # Passos per volta del motor a l'eix de sortida, considerant reducció i mode half step
            self.passos_per_volta = round(self.passos_per_volta_motor * self.reduccio_engranatge * 2) 
            self.min_angle_per_step = 360.0 / self.passos_per_volta
        elif self.mode_passos == 'full':
            self.num_pasos_seq = self.num_pins_control # 4 passos per cicle (full step)
            # Passos per volta del motor a l'eix de sortida, considerant reducció
            self.passos_per_volta = round(self.passos_per_volta_motor * self.reduccio_engranatge)
            self.min_angle_per_step = 360.0 / self.passos_per_volta

        self.posicio_actual_passos = 0 # La variable que emmagatzema la posició actual absoluta del motor en "mig-passos efectius"
        
        print(f"Motor '{self.nom}' inicialitzat internament.")
        print(f"  Pins de control: {self.pins_in}")
        print(f"  Mode de passos: {self.mode_passos}")
        print(f"  Passos per volta completa (eix de sortida): {self.passos_per_volta}")
        print(f"  Posició actual inicial: {self.posicio_actual_passos} passos.")

    def __enter__(self):
        """
        Configura els pins GPIO quan s'entra al bloc 'with'.
        """
        print(f"Motor '{self.nom}': Entrant al context (configurant GPIOs).")
        self.setup_gpio()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Neteja els pins GPIO quan se surt del bloc 'with',
        independentment de si hi ha hagut una excepció.
        """
        print(f"Motor '{self.nom}': Sortint del context (alliberant motor i netejant GPIOs).")
        self.cleanup_gpio()
        # No suprimim l'excepció si n'hi ha.

    def __del__(self):
        """
        Mètode finalitzador per assegurar la neteja de GPIO si l'objecte
        és destruït pel recol·lector d'escombraries sense usar 'with'.
        """
        if self._is_setup: # Només intentar netejar si els pins han estat configurats
            print(f"Motor '{self.nom}': Executant __del__ (netejant GPIOs com a salvaguarda).")
            self.cleanup_gpio()

    def setup_gpio(self):
        """
        Configura els pins GPIO per al motor pas a pas.
        """
        if not self._is_setup:
            print(f"Motor '{self.nom}': Configurant pins GPIO {self.pins_in}...")
            try:
                GPIO.setmode(GPIO.BCM) # Utilitza la numeració BCM dels pins
                for pin in self.pins_in:
                    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW) # Configura i posa a LOW per defecte
                self._is_setup = True
                print(f"Motor '{self.nom}': Pins GPIO configurats correctament.")
            except Exception as e:
                print(f"ERROR: No s'han pogut configurar els pins GPIO per al motor '{self.nom}': {e}")
                self._is_setup = False
        else:
            print(f"Motor '{self.nom}': Els pins GPIO ja estan configurats.")

    def _desenergitzar_pins(self):
        """
        Posa tots els pins del motor a LOW per desenergitzar les bobines.
        """
        if self._is_setup:
            for pin in self.pins_in:
                GPIO.output(pin, GPIO.LOW)
            print(f"Motor '{self.nom}': Bobines desenergitzades.")
        else:
            print(f"Motor '{self.nom}': Pins no configurats, no es pot desenergitzar.")


    def cleanup_gpio(self):
        """
        Neteja els pins GPIO específics utilitzats per aquest motor.
        Desenergiza el motor i allibera els seus recursos GPIO.
        """
        if self._is_setup:
            print(f"Motor '{self.nom}': Netejant pins GPIO {self.pins_in}...")
            self._desenergitzar_pins() # Desenergitzar abans de netejar

            try:
                # Neteja només els pins específics d'aquest motor.
                # Nota: GPIO.cleanup() sense arguments neteja TOTS els pins.
                # Si vols netejar només els teus pins, hauries de portar un registre
                # dels pins configurats i fer cleanup individualment si la llibreria ho permet.
                # No obstant això, GPIO.cleanup() generalment neteja tot el que s'ha configurat.
                # Per a la màxima seguretat i si només tens un motor, GPIO.cleanup() al final del programa principal és el més comú.
                # Aquí, farem una neteja de tot per simplicitat si la classe és la responsable.
                # Si tens més motors, el `GPIO.cleanup()` final del script principal és millor.
                GPIO.cleanup(self.pins_in) # Neteja els pins d'aquesta instància
                self._is_setup = False
                print(f"Motor '{self.nom}': Neteja de GPIO completada per als pins {self.pins_in}.")
            except RuntimeWarning as w:
                print(f"Advertència durant la neteja del pin {self.pins_in}: {w}")
            except Exception as e:
                print(f"Error inesperat durant la neteja del pin {self.pins_in}: {e}")
        else:
            print(f"Motor '{self.nom}': Pins no configurats, no es pot netejar.")

    def _set_pin_states(self, pins_to_set: list):
        """
        Configura l'estat dels pins GPIO segons el patró donat.
        """
        if not self._is_setup:
            print(f"ERROR: El motor '{self.nom}' no està configurat. No es poden establir els estats dels pins.")
            return

        for i in range(self.num_pins_control):
            try:
                GPIO.output(self.pins_in[i], pins_to_set[i])
            except Exception as e:
                print(f"ERROR al configurar el pin {self.pins_in[i]}: {e}")

    def _get_step_pattern(self, step_index: int) -> list:
        """
        Genera el patró de pins per a un índex de pas donat, envoltant la seqüència.
        Aquesta funció implementa la lògica de generació dinàmica.
        """
        normalized_step_index = step_index % self.num_pasos_seq
        
        output = [0] * self.num_pins_control

        if self.mode_passos == 'full':
            output[normalized_step_index] = 1
        elif self.mode_passos == 'half':
            if normalized_step_index % 2 == 0:
                output[normalized_step_index // 2] = 1
            else:
                pos1 = normalized_step_index // 2
                pos2 = (pos1 + 1) % self.num_pins_control
                output[pos1] = 1
                output[pos2] = 1
        return output

    def _calculate_delay_from_speed(self, velocitat_graus_per_segon: float) -> float:
        """
        Converteix la velocitat (graus/segon) a un delay (segons/pas).

        Args:
            velocitat_graus_per_segon (float): Velocitat desitjada en graus per segon.

        Returns:
            float: Temps de retard en segons per cada pas del motor.
        """
        if velocitat_graus_per_segon <= 0:
            raise ValueError("La velocitat en graus/segon ha de ser un valor positiu.")
        
        passos_per_grau = self.passos_per_volta / 360.0
        velocitat_passos_per_segon = velocitat_graus_per_segon * passos_per_grau
        
        # Establir un límit inferior per a la velocitat per evitar delays extremadament llargs
        MIN_VELOCITAT_PASSOS_PER_SEGON = 0.1 # Per exemple, 0.1 passos/segon
        if velocitat_passos_per_segon < MIN_VELOCITAT_PASSOS_PER_SEGON:
            print(f"Advertència: Velocitat massa baixa ({velocitat_graus_per_segon} graus/s), ajustant a la mínima {MIN_VELOCITAT_PASSOS_PER_SEGON/passos_per_grau:.2f} graus/s.")
            velocitat_passos_per_segon = MIN_VELOCITAT_PASSOS_PER_SEGON
            
        delay = 1.0 / velocitat_passos_per_segon
        return delay

    def release_motor(self):
        """
        Mètode públic per desenergitzar manualment el motor (posar tots els pins a LOW).
        """
        print(f"Motor '{self.nom}': Desenergitzant bobines del motor manualment...")
        self._desenergitzar_pins()

    def moure_n_passos(self, passos: int, direccio: bool, velocitat_graus_per_segon: float = 60.0):
        """
        Mou el motor un nombre determinat de passos.

        Args:
            passos (int): Nombre de passos a moure (valor absolut).
            direccio (bool): True per direcció endavant (horari), False per enrere (anti-horari).
            velocitat_graus_per_segon (float): Velocitat desitjada en graus per segon.
        """
        if not self._is_setup:
            print(f"ERROR: El motor '{self.nom}' no està configurat. No es pot moure.")
            return

        if not isinstance(passos, int) or passos < 0:
            raise ValueError("`passos` ha de ser un enter no negatiu.")
        
        delay = self._calculate_delay_from_speed(velocitat_graus_per_segon)

        print(f"Motor '{self.nom}': Movent {passos} passos cap a {'endavant' if direccio else 'enrere'} a {velocitat_graus_per_segon} graus/segon (delay: {delay:.4f}s/pas)...")

        for _ in range(passos):
            if direccio == self.DIRECCIO_ENDAVANT:
                self.posicio_actual_passos += 1
            else: # DIRECCIO_ENRERE
                self.posicio_actual_passos -= 1
            
            step_pattern = self._get_step_pattern(self.posicio_actual_passos)
            self._set_pin_states(step_pattern)
            time.sleep(delay)
        
        # Desenergitzar les bobines al final del moviment per estalviar energia i evitar sobreescalfament.
        self._desenergitzar_pins() 

        print(f"Motor '{self.nom}': Moviment de {passos} passos completat. Posició actual: {self.posicio_actual_passos} passos.")


    def moure_n_graus(self, graus: float, direccio: bool, velocitat_graus_per_segon: float = 60.0):
        """
        Mou el motor un nombre determinat de graus.

        Args:
            graus (float): Quantitat de graus a moure.
            direccio (bool): True per direcció endavant (horari), False per enrere (anti-horari).
            velocitat_graus_per_segon (float): Velocitat desitjada en graus per segon. 
        """
        if not self._is_setup:
            print(f"ERROR: El motor '{self.nom}' no està configurat. No es pot moure.")
            return

        if not isinstance(graus, (int, float)) or graus < 0:
            raise ValueError("`graus` ha de ser un valor numèric no negatiu.")

        passos_a_moure = round((graus / 360.0) * self.passos_per_volta)
        if passos_a_moure == 0 and graus > 0: # Assegura que petits moviments no s'ignorin completament
            passos_a_moure = 1

        print(f"Motor '{self.nom}': Calculats {passos_a_moure} passos per {graus:.2f} graus.")
        self.moure_n_passos(passos_a_moure, direccio, velocitat_graus_per_segon)

    def moure_a_graus(self, graus_objectiu: float, velocitat_graus_per_segon: float = 60.0):
        """
        Mou el motor a una posició angular absoluta (0-359.99 graus).

        Args:
            graus_objectiu (float): Posició angular objectiu en graus.
            velocitat_graus_per_segon (float): Velocitat desitjada en graus per segon.
        """
        if not self._is_setup:
            print(f"ERROR: El motor '{self.nom}' no està configurat. No es pot moure.")
            return

        if not isinstance(graus_objectiu, (int, float)):
            raise ValueError("`graus_objectiu` ha de ser un valor numèric.")
        posicio_antiga_graus = self.obtenir_posicio_graus()
        # Converteix la posició actual en passos a graus 
        graus_a_moure = graus_objectiu - self.obtenir_posicio_graus()

        # Si graus_a_moure és 0, ja estem a la posició. Però pot ser 0 per arrodoniment, i volíem moure.
        # Ho gestionem a moure_n_graus.
        if abs(graus_a_moure) < (self.min_angle_per_step/2): # Si la diferència és menor que mig pas
            print(f"Motor '{self.nom}': Ja a la posició objectiu de {graus_objectiu:.2f} graus (diferència insignificant).")
            return

        # Decideix la direcció més curta
        direccio = self.DIRECCIO_ENDAVANT
        if graus_a_moure < 0:
            direccio = self.DIRECCIO_ENRERE
            # Com el camí ENRERE graus_a_moure es negetiu, s'ha de cambiar
            graus_a_moure = abs(graus_a_moure)
        
        print(f"Motor '{self.nom}': De {posicio_antiga_graus:.2f} graus a {graus_objectiu:.2f} graus. Movent {graus_a_moure:.2f} graus.")
        self.moure_n_graus(graus_a_moure, direccio, velocitat_graus_per_segon)
        
    def calibrar(self, grausAMoure: float = 0.0, direccio_calibratge: bool = DIRECCIO_ENRERE, velocitat_graus_per_segon: float = 60.0):
        """
        Calibra el motor movent-lo fins a un punt de referència (simulat)
        i ajustant la posició actual a 0.

        **Nota:** En una aplicació real, aquesta funció hauria de connectar-se
        a un sensor de final de carrera (endstop switch) per detectar el punt zero.
        Aquí es simula movent un nombre màxim de passos.

        Args:
            grausAMoure (float): Nombre màxim de graus per moure's abans de calibrar a 0.
                                 Evita que el motor giri indefinidament si no hi ha sensor.
            direccio_calibratge (bool): Direcció en la qual el motor es mourà per trobar el punt de calibratge.
            velocitat_graus_per_segon (float): Velocitat desitjada en graus per segon durant el calibratge.
        """
        if not self._is_setup:
            print(f"ERROR: El motor '{self.nom}' no està configurat. No es pot calibrar.")
            return

        print(f"Motor '{self.nom}': Iniciant calibratge (movent en direcció {'endavant' if direccio_calibratge else 'enrere'})...")

        # **Implementació simulada (sense sensor real):**
        print(f"Simulant calibratge: movent {grausAMoure} passos i establint la posició a 0.")
        self.moure_n_graus(grausAMoure, direccio_calibratge, velocitat_graus_per_segon)
        self.posicio_actual_passos = 0 # Un cop "trobat" el final de carrera, la posició és 0

        print(f"Motor '{self.nom}': Calibrat. Posició actual establerta a {self.posicio_actual_passos} passos.")

    def obtenir_posicio_graus(self) -> float:
        """
        Retorna la posició actual del motor en graus.
        """
        # Sense normalitzar
        return self.posicio_actual_passos * (360.0 / self.passos_per_volta)

    def obtenir_posicio_passos(self) -> int:
        """
        Retorna la posició actual del motor en passos.
        """
        return self.posicio_actual_passos

    def obtenir_posicio_graus_normalitzada(self) -> float:
        """
        Retorna la posició actual del motor en graus, normalitzada entre 0 i 359.99.
        Útil per a la representació visual en una sola volta.
        """
        pos_graus = self.obtenir_posicio_graus() # Obtenim la posició absoluta
        normalitzat = pos_graus % 360
        if normalitzat < 0: # Assegura que el resultat sigui sempre positiu
            normalitzat += 360
        return normalitzat
