arecord ->(linia de comandes)
subproces->(per cridar lineas de comandes)
?venv?
?sudo apt update
sudo apt install python3-venv python3-pip alsa-utils
python3 -m venv venv
source venv/bin/activate?
?llibreries extres?


modificar
/boot/firmware/config.txt:"
#For more options and information see
#http://rptl.io/configtxt
#Some settings may impact device functionality. See link above for details

#Uncomment some or all of these to enable the optional hardware interfaces
#dtparam=i2c_arm=on
dtparam=i2s=on
#dtparam=spi=on

#Microfon
#test dtoverlay=dmic-overlay
#test dtoverlay=hifiberry-dacplus
#test dtoverlay=iqaudio-codec
dtoverlay=googlevoicehat-soundcard

#Enable audio (loads snd_bcm2835)
dtparam=audio=on
"
