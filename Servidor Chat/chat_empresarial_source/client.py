"""Punto de entrada de la aplicación cliente del chat empresarial."""

import argparse

from chat_client.config import load_server_config
from chat_client.ui import ChatApp


def parse_args():
    """Lee configuración y permite sobreescribirla opcionalmente por terminal."""
    # La configuración JSON permite abrir la app con doble clic, sin escribir la IP.
    default_host, default_port = load_server_config()

    parser = argparse.ArgumentParser(
        description="Cliente gráfico para la sala de chat empresarial TCP."
    )
    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Dirección IP o nombre del servidor. Configurada: {default_host}",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Puerto TCP del servidor. Configurado: {default_port}",
    )
    return parser.parse_args()


def main():
    """Crea la misma interfaz original y la conecta al servidor configurado."""
    args = parse_args()
    app = ChatApp(host=args.host, port=args.port)
    app.run()


if __name__ == "__main__":
    main()
