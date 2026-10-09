#!/bin/sh
# Inicia el cliente usando el host/puerto guardados en client_config.json.
cd "$(dirname "$0")" || exit 1
exec python3 client.py
