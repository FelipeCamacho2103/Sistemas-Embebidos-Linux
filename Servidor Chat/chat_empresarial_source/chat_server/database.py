"""Persistencia SQL del historial del chat usando SQLite.

SQLite sigue siendo una base de datos SQL, pero no necesita instalar un motor
separado. El archivo .db queda en el servidor y conserva el historial aun si el
proceso se cierra o el computador se reinicia.
"""

import sqlite3
from pathlib import Path


class ChatDatabase:
    """Encapsula las operaciones SQL necesarias para el historial."""

    def __init__(self, database_path):
        # Guardamos una ruta absoluta para que el servidor siempre abra el mismo archivo.
        self.database_path = Path(database_path).expanduser().resolve()
        # Creamos la carpeta padre si todavía no existe.
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        # Creamos la tabla e índices al construir el objeto.
        self.initialize()

    def _connect(self):
        """Abre una conexión independiente; es seguro usarla desde varios hilos."""
        connection = sqlite3.connect(self.database_path, timeout=10)
        # Row permite acceder a las columnas por nombre además de por posición.
        connection.row_factory = sqlite3.Row
        # Espera un poco si otra escritura mantiene temporalmente bloqueada la BD.
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def initialize(self):
        """Crea la estructura SQL sin borrar información que ya exista."""
        with self._connect() as connection:
            # WAL mejora la convivencia entre lecturas de historial y nuevas escrituras.
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    text TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            # El índice ayuda a recuperar mensajes cronológicamente si la tabla crece.
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)"
            )
            connection.commit()

    def add_message(self, sender, text, timestamp):
        """Inserta un mensaje y devuelve el ID permanente generado por SQLite."""
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO messages(sender, text, timestamp) VALUES (?, ?, ?)",
                (sender, text, timestamp),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def get_history(self):
        """Devuelve todo el historial ordenado por ID ascendente."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, sender, text, timestamp FROM messages ORDER BY id ASC"
            ).fetchall()

        # Convertimos las filas SQL al mismo formato JSON que ya entiende la interfaz.
        return [
            {
                "id": int(row["id"]),
                "sender": row["sender"],
                "text": row["text"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
