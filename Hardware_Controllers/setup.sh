#!/bin/bash

# Comprova si la carpeta existeix
if [ -d "venv" ]; then
  # Si 'venv' existeix, no fa res (o podries posar-hi un missatge, per exemple)
  echo "La carpeta 'venv' ja existeix."
else
  # Si 'venv' NO existeix, executa l'script per crear-la
  . ./crear_venv.sh
fi

# Activa l'entorn virtual (independentment de si s'ha creat ara o ja existia)
. ./activar_venv.sh

# Executa el teu programa principal de Python
python main.py

# Desactiva l'entorn virtual
. ./desactivar_venv.sh