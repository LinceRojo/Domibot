# Configuració de l'Amplificador Adafruit TPA2016 amb Raspberry Pi 4 Model B

Aquesta guia detalla els passos per connectar i controlar l'amplificador d'àudio estèreo Adafruit TPA2016 amb una Raspberry Pi 4 Model B, utilitzant la comunicació I2C i la sortida d'àudio analògica.


1. Connexions Físiques
La primera i més important part és el cablejat correcte segons la documentació d'Adafruit:

    * Alimentació de l'Amplificador:
       - TPA2016 VDD → Raspberry Pi 3.3V (Pin 1) o 5V (Pin 2 o 4).
       - TPA2016 GND → Raspberry Pi GND (per exemple, Pin 6).

   * Control I2C (Comunicació Digital):
       - TPA2016 SDA → Raspberry Pi GPIO 2 / SDA (Pin 3).
       - TPA2016 SCL → Raspberry Pi GPIO 3 / SCL (Pin 5).
       - TPA2016 I2C VCC → Raspberry Pi 3.3V (Pin 1). Això assegura que la lògica I2C funcioni a 3.3V, compatible amb la Pi.
       - TPA2016 ADD: Deixar sense connectar (l'amplificador utilitza l'adreça I2C per defecte 0x58).

   * Entrada d'Àudio (des del Jack de 3.5mm de la Pi):// com nomes tinc un altabeu e conectat nomes el L
       - Raspberry Pi Jack 3.5mm Canal Esquerre → TPA2016 L+
       - Raspberry Pi Jack 3.5mm Canal Dret → TPA2016 R+
       - Raspberry Pi Jack 3.5mm Terra → TPA2016 L- i TPA2016 R- (connectar ambdues entrades negatives a la terra de la Pi).

   * Sortida a Altaveus:// com nomes tinc un altabeu e conectat nomes el L
       - Conecta els altaveus de 4 a 8 ohms als terminals de sortida de l'amplificador (R+/R- i L+/L-).

 -------------------

  2. Pas 1: Configuració Bàsica de la Raspberry Pi

  - Primer, assegurem-nos que la teva Raspberry Pi està preparada per comunicar-se amb l'amplificador.

   * Obre una Terminal: Accedeix a la línia de comandes de la teva Raspberry Pi.

   * Habilita la interfície I2C: L'amplificador TPA2016 es controla per I2C, així que hem d'assegurar-nos que estigui activada a la teva Pi.

Bash

    sudo raspi-config

   * Ves a 3 Interface Options (Opcions d'Interfície).
   * Selecciona I5 I2C i tria Yes (Sí) per habilitar-ho.
   * Surt de raspi-config i reinicia la Raspberry Pi si se't demana.

-------------------

  3.Pas 1: Investigar i Configurar la Sortida d'Àudio Correctament
Com que amixer cset numid=3 1 no funciona, anem a utilitzar alsamixer, que és una interfície més visual i interactiva per controlar l'àudio a la terminal.

   * Instal·la alsamixer i aplay (si no els tens ja):
Bash

    sudo apt update
    sudo apt install alsa-utils

Això instal·larà alsamixer i aplay, que ens seran útils.

   * Llista les targetes de so disponibles:
Això ens ajudarà a confirmar que la Raspberry Pi detecta la seva pròpia targeta de so interna.
Bash

    aplay -l

Hauries de veure una sortida similar a aquesta (el número de la targeta i el nom poden variar lleugerament):

    **** List of PLAYBACK Hardware Devices ****
    card 0: b1 [bcm2835 HDMI 1], device 0: bcm2835 HDMI 1 [bcm2835 HDMI 1]
      Subdevices: 8/8
      ...
    card 0: b1 [bcm2835 HDMI 1], device 1: bcm2835 HDMI 2 [bcm2835 HDMI 2]
      Subdevices: 8/8
      ...
    card 1: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
      Subdevices: 8/8
      ...

Fixa't en la línia que diu Headphones o bcm2835 Headphones. El número de la targeta (card X) és important. Normalment és 1.

  * Obre alsamixer:
Ara, obre la interfície alsamixer per controlar el volum.

Bash

    alsamixer -c 1 # Utilitza el número de la targeta que hagis vist per "Headphones" amb aplay -l, normalment és 1

Si el número de targeta no és 1, utilitza el correcte. Si no estàs segur, simplement prova alsamixer.

Un cop dins d' alsamixer:

      - Hauries de veure una interfície gràfica amb barres de volum.
      - Utilitza les tecles de fletxa esquerra/dreta per seleccionar el control de volum principal (sovint anomenat "PCM" o "Headphone").
      - Utilitza les tecles de fletxa amunt/avall per pujar o baixar el volum. Assegura't que el volum no estigui a 0 o "MM" (mut). Si veus "MM", prem la tecla M per desmutar-lo.
      - Un cop hagis ajustat el volum, prem Esc per sortir d'alsamixer.

  * Guarda la configuració d'àudio (opcional, però recomanat):
Perquè aquests ajustos es mantinguin després de reiniciar la Pi:

Bash

    sudo alsactl store


 -----------------


 4. Reprodueix àudio a la Raspberry Pi:
Per comprovar-ho, pots reproduir una cançó, un arxiu de so, o fins i tot generar un so simple.

    * Des d'un fitxer MP3 o WAV:
        - Instal·la mpg123 (per a MP3) o aplay (per a WAV):

Bash

    sudo apt install mpg123

 * a continuacio:
      - Descarrega un arxiu de so de prova, per exemple: wget https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3
      - Reprodueix-lo:

Bash

    mpg123 SoundHelix-Song-1.mp3 (o aplay un_arxiu.wav)
 
