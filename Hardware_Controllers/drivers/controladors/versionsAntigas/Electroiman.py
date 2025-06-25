import RPi.GPIO as GPIO

class Electroiman:

    def __init__(self, pin_control: int):
        self.pin_control = pin_control
        self._actiu = False
        self._construit = False # Indica si el pin GPIO ha estat configurat correctament
        self.setup() # Configurem el pin en la inicialització
        print(f"Electroimant inicialitzat (pin: {self.pin_control})")

    def __del__(self):
        """
        Es crida quan l'objecte Electroiman està a punt de ser destruït.
        Assegura que els pins GPIO es netegen correctament.
        """
        print(f"Executant __del__ per a l'electroimant del pin {self.pin_control}")
        self.cleanup()

    def __enter__(self):
        """
        Permet utilitzar la classe amb la sentència 'with'.
        Assegura que el pin es configura abans d'entrar al bloc de codi.
        """
        if not self._construit:
            self.setup() # Assegurem que el pin estigui configurat si no ho està
        return self # Retorna l'objecte per poder-lo usar amb 'as'

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        S'executa quan es surt del bloc 'with', fins i tot si hi ha una excepció.
        Garanteix la neteja dels pins GPIO.
        """
        print(f"Sortint del context de l'electroimant (pin: {self.pin_control})")
        self.cleanup()
        # Per defecte, no suprimim l'excepció si n'hi ha.

    def setup(self):
        """
        Configura el pin GPIO si encara no ha estat configurat.
        Estableix el mode de numeració i la direcció del pin.
        """
        if not self._construit: # Més Pythonic que '== False'
            print(f"Configurant pin GPIO {self.pin_control} per a l'electroimant.")
            try:
                GPIO.setmode(GPIO.BCM)
                # IMPORTANT: Inicialitzar el pin a LOW per seguretat
                GPIO.setup(self.pin_control, GPIO.OUT, initial=GPIO.LOW)
                self._construit = True # Marcat com a construït només si la configuració té èxit
            except Exception as e:
                print(f"ERROR: No s'ha pogut configurar el pin {self.pin_control}: {e}")
                self._construit = False # Si hi ha un error, no el marquem com a construït
        else:
            print(f"El pin {self.pin_control} ja està configurat.")

    def cleanup(self):
        """
        Neteja el pin GPIO utilitzat per aquest electroimant.
        Desactiva l'electroimant i allibera el pin.
        """
        if self._construit: # Més Pythonic que '== True'
            print(f"Netejant pin GPIO {self.pin_control} per a l'electroimant.")
            # Primer intentem desactivar-lo per seguretat
            if self._actiu:
                self.desactivar()
            try:
                GPIO.cleanup(self.pin_control)
                self._construit = False # Marquem com a no construït un cop netejat
            except RuntimeWarning as w:
                print(f"Advertència durant la neteja del pin {self.pin_control}: {w}")
            except Exception as e:
                print(f"Error inesperat durant la neteja del pin {self.pin_control}: {e}")
        else:
            print(f"El pin {self.pin_control} no s'ha configurat amb èxit o ja s'ha netejat, no es pot netejar.")

    def activar(self):
        """
        Activa l'electroimant (estableix el pin a HIGH).
        Retorna True si l'activació és exitosa, False en cas contrari.
        """
        print(f"Electroimant (pin {self.pin_control}): ACTIVANT")
        if not self._construit:
            print(f"ERROR: El pin {self.pin_control} no està configurat. No es pot activar.")
            return False
        try:
            GPIO.output(self.pin_control, GPIO.HIGH)
            self._actiu = True # Només actualitzem l'estat si l'operació és exitosa
            print(f"Electroimant (pin {self.pin_control}): ACTIVAT (correctament)")
            return True
        except Exception as e:
            print(f"S'ha produït un error en activar (pin {self.pin_control}): {e}")
            self._actiu = False # Si falla, assegurem que l'estat intern és False
            return False

    def desactivar(self):
        """
        Desactiva l'electroimant (estableix el pin a LOW).
        Retorna True si la desactivació és exitosa, False en cas contrari.
        """
        print(f"Electroimant (pin {self.pin_control}): DESACTIVANT")
        if not self._construit:
            print(f"ERROR: El pin {self.pin_control} no està configurat. No es pot desactivar.")
            return False
        try:
            GPIO.output(self.pin_control, GPIO.LOW)
            self._actiu = False # Només actualitzem l'estat si l'operació és exitosa
            print(f"Electroimant (pin {self.pin_control}): DESACTIVAT (correctament)")
            return True
        except Exception as e:
            print(f"S'ha produït un error en desactivar (pin {self.pin_control}): {e}")
            # Si falla, l'estat real del pin pot ser encara actiu.
            # L'estat _actiu no es canvia a False en cas d'error aquí,
            # ja que la desactivació no es va garantir.
            return False

    def estat_actiu(self) -> bool:
        """
        Retorna l'estat actual de l'electroimant (True si està actiu, False si no).
        """
        return self._actiu
