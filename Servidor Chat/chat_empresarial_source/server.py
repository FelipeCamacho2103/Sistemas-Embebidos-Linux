"""Punto de entrada del servidor persistente del chat empresarial."""

import argparse
from pathlib import Path

from chat_server.server import ChatServer


def parse_args():
    """Define red y ubicación del archivo SQL desde argumentos administrables."""
    default_database = Path(__file__).resolve().parent / "data" / "chat_history.db"

    parser = argparse.ArgumentParser(
        description="Servidor TCP persistente para el chat empresarial."
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Interfaz de escucha. 0.0.0.0 acepta clientes de la LAN.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Puerto TCP del chat. Por defecto: 5000.",
    )
    parser.add_argument(
        "--database",
        default=str(default_database),
        help="Ruta del archivo SQLite persistente.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    server = ChatServer(host=args.host, port=args.port, database_path=args.database)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido por el administrador.")


if __name__ == "__main__":
    main()
