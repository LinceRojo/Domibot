import subprocess
import sounddevice as sd

# Mostrar dispositivos disponibles
print("🎧 Dispositivos de entrada disponibles:\n")
devices = sd.query_devices()
input_devices = []

for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f"{i}: {dev['name']} ({dev['max_input_channels']} canales)")
        input_devices.append(i)

# Elegir dispositivo
while True:
    try:
        device_index = int(input("\n🔢 Elegí el número del dispositivo que querés usar: "))
        if device_index in input_devices:
            break
        else:
            print("❌ Número inválido. Probá de nuevo.")
    except ValueError:
        print("❌ Ingresá un número.")

# Pedir configuración de grabación
filename = input("💾 Nombre del archivo (ej. grabacion.wav): ").strip()
if not filename:
    filename = "grabacion.wav"

try:
    duration = int(input("⏱️ Duración en segundos (ej. 5): "))
except ValueError:
    duration = 5

try:
    samplerate = int(input("🎚️ Frecuencia de muestreo en Hz (ej. 16000): "))
except ValueError:
    samplerate = 16000

try:
    channels = int(input("🔈 Número de canales (1 = mono, 2 = estéreo): "))
    if channels not in [1, 2]:
        raise ValueError
except ValueError:
    channels = 1

# Formato (por defecto 16-bit)
fmt = input("📦 Formato de muestra [S16_LE, S32_LE] (por defecto S16_LE): ").strip().upper()
if fmt not in ["S16_LE", "S32_LE"]:
    fmt = "S16_LE"

# Comando arecord
print("\n🎙️ Grabando con arecord...")
subprocess.run([
    "arecord",
    "-D", f"plughw:{device_index},0",
    "-c", str(channels),
    "-r", str(samplerate),
    "-f", fmt,
    "-d", str(duration),
    filename
])

print(f"\n✅ Archivo guardado como: {filename}")
