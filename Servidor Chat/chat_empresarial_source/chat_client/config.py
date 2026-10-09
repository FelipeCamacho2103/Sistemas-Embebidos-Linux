"""Carga la dirección del servidor sin añadir controles nuevos a la interfaz.

La interfaz gráfica se mantiene intacta. La IP/host y el puerto se leen de un
archivo JSON para que el usuario pueda abrir la aplicación y conectarse sin
escribir parámetros en una terminal.
"""

import json
import sys
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"  # Valor seguro para pruebas en el mismo computador.
DEFAULT_PORT = 5000          # Puerto TCP usado por el servidor del proyecto.


def _candidate_config_paths():
    """Devuelve, en orden, los lugares donde puede existir la configuración."""
    # En una instalación Debian, el administrador configura este archivo una vez.
    yield Path("/etc/chat-empresarial/client_config.json")

    # En modo fuente/portable, el JSON puede vivir junto a client.py.
    project_file = Path(__file__).resolve().parent.parent / "client_config.json"
    yield project_file

    # Si algún día se genera un binario, también aceptamos config junto al ejecutable.
    if getattr(sys, "frozen", False):
        yield Path(sys.executable).resolve().parent / "client_config.json"


def load_server_config():
    """Carga host/puerto; si no hay archivo válido usa los valores por defecto."""
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    for path in _candidate_config_paths():
        if not path.is_file():
            continue

        try:
            with path.open("r", encoding="utf-8") as config_file:
                data = json.load(config_file)

            configured_host = str(data.get("host", host)).strip()
            configured_port = int(data.get("port", port))

            if configured_host:
                host = configured_host
            if 1 <= configured_port <= 65535:
                port = configured_port

            # El primer archivo válido tiene prioridad sobre los siguientes.
            break
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # Un archivo dañado no impide iniciar la app; se intenta el siguiente.
            continue

    return host, port
