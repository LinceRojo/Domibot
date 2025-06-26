La taula descriu les funcions alternatives dels pins GPIO (General Purpose Input/Output). Això vol dir que cada pin físic pot fer diverses coses, no només ser una simple entrada o sortida digital.

Explicació de les Columnes:

   - GPIO: Aquest és el número del pin GPIO segons la numeració BCM (Broadcom). Per exemple, GPIO0, GPIO1, GPIO4, etc. Aquests són els pins que pots controlar des del teu programari.

   - Pull: Indica l'estat de la resistència interna de pull-up o pull-down per defecte quan el pin s'engega o no està configurat activament.
        High: Té una resistència de pull-up activada per defecte. Si no hi connectes res i el configures com a entrada, llegirà un valor alt (normalment 3.3V).
        Low: Té una resistència de pull-down activada per defecte. Si no hi connectes res i el configures com a entrada, llegirà un valor baix (0V o GND).
        Això és important sobretot quan uses els pins com a entrades per evitar que "flotin" entre estats. Per a sortides, no sol afectar directament el seu funcionament bàsic.

   - ALT0, ALT1, ALT2, ALT3, ALT4, ALT5: Aquestes són les Funcions Alternatives. El processador del Raspberry Pi té diversos mòduls interns (com controladors I2C, SPI, UART, PWM, etc.). Aquests mòduls necessiten connectar-se al món exterior a través dels pins físics. Com que hi ha més funcions internes que pins, molts pins poden realitzar diferents tasques especialitzades.
        Cada columna ALT representa un "mode" diferent per al pin. Quan configures un pin per utilitzar, per exemple, la seva funció ALT0, farà la tasca específica llistada en aquesta columna (p. ex., SDA0 per a GPIO0 en mode ALT0).
        Només pots activar una funció a la vegada per a cada pin: o bé funciona com a GPIO bàsic (entrada/sortida digital), o bé fa una de les seves funcions alternatives (ALT0 a ALT5).

Com Utilitzar els Pins com a Sortides Digitals:

   - Qualsevol pin llistat a la columna "GPIO" (de GPIO0 a GPIO27 en aquesta taula) pot ser utilitzat com una sortida digital estàndard.

   - Per fer-ho, no has d'activar cap de les funcions alternatives (ALT0 a ALT5). Simplement, has d'utilitzar una llibreria de programació (com RPi.GPIO o gpiozero en Python, o wiringPi en C/C++) per:
        Configurar el pin desitjat com a SORTIDA (OUTPUT).
        Establir el seu valor a ALT (HIGH, normalment 3.3V) o BAIX (LOW, 0V/GND).

   - En resum: Si vols una sortida digital simple, tria qualsevol pin GPIO que et vagi bé físicament i que no estigui sent utilitzat per alguna altra funció del sistema que hagis habilitat (com la consola sèrie per defecte als pins 14/15, o I2C si l'has activat als pins 2/3). Configura'l com a sortida al teu codi i ja està.

Entenent les Funcions Alternatives:

Si en un futur necessites funcions més específiques, hauràs de consultar aquesta taula:

   - I2C: Si vols comunicar-te amb un dispositiu I2C, normalment utilitzaràs SDA (dades) i SCL (rellotge). La taula mostra diverses opcions:
        I2C0: SDA0 (GPIO0, ALT0) i SCL0 (GPIO1, ALT0) - Aquest és el bus I2C principal i més comú.
        I2C1: SDA1 (GPIO2, ALT0) i SCL1 (GPIO3, ALT0)
        Hi ha més busos I2C disponibles en altres pins i modes ALT (I2C3, I2C4, I2C5, I2C6).
   - SPI: Per a comunicació SPI (Serial Peripheral Interface), necessites MOSI (Master Out Slave In), MISO (Master In Slave Out), SCLK (Serial Clock) i CE (Chip Enable, sovint anomenat CS - Chip Select).
        SPI0: GPIOs 7, 8, 9, 10, 11 en mode ALT0.
        SPI1, SPI3, SPI4, SPI5, SPI6: Disponibles en altres pins i modes ALT.
   - UART (Port Sèrie): Per a comunicació sèrie asíncrona, necessites TXD (Transmetre Dades) i RXD (Rebre Dades).
        UART0: TXD0 (GPIO14, ALT0) i RXD0 (GPIO15, ALT0) - Sovint usat per la consola sèrie.
        Hi ha altres UARTs (UART1 a UART5) disponibles en altres pins/ALT modes.
   - PWM (Pulse Width Modulation): Per controlar la potència mitjana enviada a un dispositiu (com la brillantor d'un LED o la velocitat d'un motor).
        PWM0: Disponible a GPIO12 (ALT0), GPIO18 (ALT5).
        PWM1: Disponible a GPIO13 (ALT0), GPIO19 (ALT5).
   - Altres funcions: La taula també llista funcions per a rellotges (GPCLK), interfície de pantalla paral·lela (DPI), interfície de targeta SD (SD), àudio PCM, etc.
