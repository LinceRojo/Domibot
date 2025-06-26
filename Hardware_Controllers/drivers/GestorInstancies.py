import threading

# Intentem importar RPi.GPIO de manera segura
#try:
import RPi.GPIO as GPIO
#except ImportError:
#    GPIO = None # Si no està disponible, posem GPIO a None per evitar errors

class GestorInstancies:
    _instancia = None
    _lock = threading.Lock()
    _instancies_registrades = {} 
    _gpio_mode_configurat = False # Nou atribut per assegurar que només es configura una vegada

    def __new__(cls):
        with cls._lock:
            if cls._instancia is None:
                cls._instancia = super(GestorInstancies, cls).__new__(cls)
                print("--- [Singleton] Instància única creada ---")
            return cls._instancia

    def __init__(self):
        # A __init__ només s'executa un cop per la naturalesa del Singleton (després de __new__)
        # Aquí podem inicialitzar atributs específics de la instància Singleton si cal
        pass # La configuració GPIO la farem a __enter__

    def __enter__(self):
        print("--- [Singleton] Entrant al context (preparant gestor principal) ---")
        # Aquí és on configurarem el mode GPIO si no s'ha fet ja
        # Ens assegurem que GPIO sigui un atribut de la instància per facilitar l'accés
        self.GPIO = GPIO # Guardem la referència a la llibreria (o None)

        # Configuració del mode GPIO: l'usuari el passarà al mètode d'inici
        # o el podríem guardar com un atribut en el constructor del Singleton si fos necessari.
        # Per simplicitat i flexibilitat, ho permetrem configurar amb un mètode.
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("--- [Singleton] Sortint del context (neteja final d'instàncies gestionades) ---")
        
        if exc_type:
            print(f"--- [Singleton] Excepció detectada al gestor principal: {exc_type.__name__}: {exc_val} ---")

        # Crida a __exit__ de cada instància registrada en ordre invers
        for nom_instancia in list(self._instancies_registrades.keys())[::-1]: 
            instancia_cm_obj = self._instancies_registrades[nom_instancia]
            print(f"--- [Singleton] Tancant instància '{nom_instancia}' via __exit__ ---")
            try:
                self._pasos_adicionals_exit(instancia_cm_obj)
                instancia_cm_obj.__exit__(exc_type, exc_val, exc_tb) 
            except Exception as e:
                print(f"--- [Singleton] ERROR al tancar instància '{nom_instancia}': {e} ---")
            
            del self._instancies_registrades[nom_instancia]
        
        self._instancies_registrades.clear()
        print("--- [Singleton] Neteja de totes les instàncies completada ---")
        
        # Neteja de GPIO quan el GestorInstancies surt
        if self.GPIO and self._gpio_mode_configurat: # Si GPIO es va configurar, fem cleanup
            self.GPIO.cleanup()
            print("Mode GPIO netejat (GPIO.cleanup()).")
            GestorInstancies._gpio_mode_configurat = False # Resetejem l'estat
        # No retornem True per propagar excepcions del gestor principal

    def _pasos_adicionals_enter(self, instancia_cm_obj):
        pass
        #if isinstance(instancia_cm_obj, ConnexioBDCM):
        #    print(f"[Singleton] Executant passos addicionals d'entrada per ConnexioBDCM: '{instancia_cm_obj.bd_nom}'")
        #    instancia_cm_obj.iniciar_pasos_adicionals()
            
    def _pasos_adicionals_exit(self, instancia_cm_obj):
        pass
        #if isinstance(instancia_cm_obj, ConnexioBDCM):
        #    print(f"[Singleton] Executant passos addicionals de sortida per ConnexioBDCM: '{instancia_cm_obj.bd_nom}'")
        #    instancia_cm_obj.finalitzar_pasos_adicionals()
            
            
    def configurar_gpio_mode(self, gpio_mode_str):
        """
        Configura el mode de numeració dels pins GPIO.
        Aquesta funció només es pot cridar un cop per instància Singleton.
        :param gpio_mode_str: El string del mode de numeració dels pins (p.ex., 'BCM' o 'BOARD').
        """
        if self.GPIO is None:
            print("Avís: RPi.GPIO no disponible. Saltant configuració GPIO.")
            return

        if self._gpio_mode_configurat:
            print("Avís: El mode GPIO ja ha estat configurat. Ignorant la nova configuració.")
            return

        try:
            if gpio_mode_str == "BCM":
                self.GPIO.setmode(GPIO.BCM)
            elif gpio_mode_str == "BOARD":
                self.GPIO.setmode(GPIO.BOARD)
            else:
                print(f"Avís: Mode GPIO '{gpio_mode_str}' no reconegut. Utilitzant BCM per defecte si GPIO està disponible.")
                if GPIO: # Aquesta comprovació és crucial i correcta
                    self.GPIO.setmode(GPIO.BCM)
            
            print(f"Mode GPIO establert a: {gpio_mode_str} (BCM={self.GPIO.BCM}, BOARD={self.GPIO.BOARD}).")
            GestorInstancies._gpio_mode_configurat = True # Marca la configuració com a feta
        except Exception as e:
            print(f"ERROR: No s'ha pogut configurar el mode GPIO: {e}")


    def crear_i_entrar_instancia(self, nom, classe_a_instanciar, *args, **kwargs):
        if nom in self._instancies_registrades:
            print(f"[Singleton] Advertència: La instància '{nom}' ja existeix. Retornant el recurs existent.")
            return self._instancies_registrades[nom].recurs_obtingut_de_enter 
            
        print(f"[Singleton] Creant i entrant a instància '{nom}' de la classe '{classe_a_instanciar.__name__}'")
        try:
            obj_context_manager = classe_a_instanciar(*args, **kwargs)
            recurs_obtingut = obj_context_manager.__enter__()
            
            obj_context_manager.recurs_obtingut_de_enter = recurs_obtingut
            self._pasos_adicionals_enter(obj_context_manager)
            
            self._instancies_registrades[nom] = obj_context_manager 
            
            return recurs_obtingut 
        except Exception as e:
            print(f"[Singleton] Error al crear o entrar a instància '{nom}': {e}")
            return None

    def obtenir_recurs(self, nom):
        instancia_cm_obj = self._instancies_registrades.get(nom)
        if instancia_cm_obj:
            return instancia_cm_obj.recurs_obtingut_de_enter 
        return None

    def sortir_i_destruir_instancia(self, nom):
        if nom in self._instancies_registrades:
            instancia_cm_obj = self._instancies_registrades[nom]
            print(f"[Singleton] Sortint i destruint instància '{nom}' de forma individual.")
            try:
                self._pasos_adicionals_exit(instancia_cm_obj)
                instancia_cm_obj.__exit__(None, None, None) 
            except Exception as e:
                print(f"[Singleton] ERROR al sortir de la instància '{nom}': {e}")
            
            del self._instancies_registrades[nom]
            return True
        print(f"[Singleton] La instància '{nom}' no estava registrada per destruir.")
        return False
