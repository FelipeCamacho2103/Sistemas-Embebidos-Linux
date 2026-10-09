#!/bin/sh
# Inicia el servidor en todas las interfaces y usa una BD persistente local.
cd "$(dirname "$0")" || exit 1
exec python3 server.py --host 0.0.0.0 --port 5000 --database ./data/chat_history.db
