"""Servidor TCP concurrente para un chat empresarial de máximo 10 personas."""

import json
import socket
import threading
from dataclasses import dataclass, field
from datetime import datetime

from .database import ChatDatabase


MAX_CLIENTS = 10          # Requisito del proyecto: máximo 10 usuarios simultáneos.
MAX_NAME_LENGTH = 24      # Debe coincidir con la validación de la interfaz actual.
MAX_MESSAGE_LENGTH = 1000 # Evita mensajes accidentalmente enormes.


@dataclass
class ClientSession:
    """Información que el servidor asocia a una conexión TCP aceptada."""

    sock: socket.socket
    name: str
    ready: bool = False
    # Cada cliente tiene su propio lock para impedir que dos hilos mezclen bytes JSON.
    send_lock: threading.Lock = field(default_factory=threading.Lock)


class ChatServer:
    """Coordina conexiones, nombres, mensajes, presencia e historial SQL."""

    def __init__(self, host, port, database_path):
        self.host = host
        self.port = port
        self.database = ChatDatabase(database_path)

        # clients_lock protege el diccionario de usuarios conectados.
        self.clients_lock = threading.RLock()
        # message_order_lock garantiza un orden global único para INSERT + broadcast.
        self.message_order_lock = threading.Lock()
        # La clave es el socket; el valor contiene nombre, estado y lock de envío.
        self.clients = {}
        self.server_socket = None
        self.running = False

    @staticmethod
    def _encode(message):
        """Serializa un diccionario como JSON UTF-8 terminado en salto de línea."""
        return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")

    def _send_to_session(self, session, message):
        """Envía un evento completo sin permitir que otro hilo intercale bytes."""
        payload = self._encode(message)
        with session.send_lock:
            session.sock.sendall(payload)

    @staticmethod
    def _send_raw(sock, message):
        """Se usa solo antes de que exista una ClientSession definitiva."""
        payload = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
        sock.sendall(payload)

    def _ready_sessions(self):
        """Toma una foto de los clientes que ya terminaron el proceso de entrada."""
        with self.clients_lock:
            return [session for session in self.clients.values() if session.ready]

    def _broadcast(self, message):
        """Envía un evento a todos los usuarios listos y limpia conexiones muertas."""
        dead_sockets = []

        for session in self._ready_sessions():
            try:
                self._send_to_session(session, message)
            except OSError:
                dead_sockets.append(session.sock)

        if dead_sockets:
            with self.clients_lock:
                for dead_sock in dead_sockets:
                    self.clients.pop(dead_sock, None)

    def _presence_event(self):
        """Construye la lista que alimenta la barra lateral existente de la UI."""
        with self.clients_lock:
            users = sorted(
                (session.name for session in self.clients.values() if session.ready),
                key=str.casefold,
            )

        return {"type": "presence", "count": len(users), "users": users}

    def _broadcast_presence(self):
        self._broadcast(self._presence_event())

    def _choose_name_locked(self, requested_name):
        """Asigna Ana, Ana2, Ana3...; se llama con clients_lock adquirido."""
        used_casefold = {
            session.name.casefold() for session in self.clients.values()
        }

        if requested_name.casefold() not in used_casefold:
            return requested_name

        suffix = 2
        while f"{requested_name}{suffix}".casefold() in used_casefold:
            suffix += 1

        return f"{requested_name}{suffix}"

    def _reserve_name(self, sock, requested_name):
        """Valida capacidad de sala y reserva un nombre único para este socket."""
        with self.clients_lock:
            if sock in self.clients:
                return None, "Ya realizaste el ingreso a la sala."

            if len(self.clients) >= MAX_CLIENTS:
                return None, "La sala está llena. Máximo 10 usuarios conectados."

            assigned_name = self._choose_name_locked(requested_name)
            session = ClientSession(sock=sock, name=assigned_name, ready=False)
            self.clients[sock] = session
            return session, None

    def _send_history(self, session):
        """Consulta SQLite y envía el historial persistente al cliente indicado."""
        history = self.database.get_history()
        self._send_to_session(session, {"type": "history", "messages": history})

    def _handle_join(self, sock, message):
        """Procesa el nombre y entrega automáticamente el historial al entrar."""
        requested_name = str(message.get("requested_name", "")).strip()

        if not requested_name:
            self._send_raw(sock, {"type": "error", "message": "El nombre no puede estar vacío."})
            return None, False

        if len(requested_name) > MAX_NAME_LENGTH:
            self._send_raw(
                sock,
                {
                    "type": "error",
                    "message": f"El nombre puede tener máximo {MAX_NAME_LENGTH} caracteres.",
                },
            )
            return None, False

        session, error = self._reserve_name(sock, requested_name)
        if error:
            self._send_raw(sock, {"type": "error", "message": error})
            # Sala llena: cerramos la conexión para no ocupar recursos sin usuario.
            return None, True

        # join_ok mantiene exactamente el contrato que ya consume la interfaz.
        self._send_to_session(
            session,
            {"type": "join_ok", "assigned_name": session.name},
        )
        # El historial llega inmediatamente, sin exigir pulsar el botón Recuperar historial.
        self._send_history(session)

        # Solo después del handshake el usuario empieza a recibir broadcasts generales.
        with self.clients_lock:
            session.ready = True

        self._broadcast({"type": "system", "message": f"{session.name} entró a la sala."})
        self._broadcast_presence()
        return session, False

    def _handle_chat(self, session, message):
        """Persiste primero y retransmite después, conservando un único orden global."""
        text = str(message.get("text", "")).strip()
        if not text:
            return

        if len(text) > MAX_MESSAGE_LENGTH:
            self._send_to_session(
                session,
                {
                    "type": "error",
                    "message": f"El mensaje puede tener máximo {MAX_MESSAGE_LENGTH} caracteres.",
                },
            )
            return

        with self.message_order_lock:
            # La hora oficial es del servidor, no del cliente.
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # SQLite genera un ID creciente que sobrevive a reinicios del servidor.
            message_id = self.database.add_message(session.name, text, timestamp)

            event = {
                "id": message_id,
                "type": "message",
                "sender": session.name,
                "text": text,
                "timestamp": timestamp,
            }
            # Solo se difunde después de que INSERT haya terminado correctamente.
            self._broadcast(event)

    def _remove_client(self, sock):
        """Libera el nombre y actualiza presencia cuando una conexión termina."""
        with self.clients_lock:
            old_session = self.clients.pop(sock, None)

        try:
            sock.close()
        except OSError:
            pass

        if old_session is not None and old_session.ready:
            self._broadcast(
                {"type": "system", "message": f"{old_session.name} salió de la sala."}
            )
            self._broadcast_presence()

    def handle_client(self, sock, address):
        """Bucle ejecutado en un hilo por cada conexión TCP aceptada."""
        session = None
        close_after_join_error = False

        try:
            # makefile permite leer un JSON por línea, tal como espera el protocolo actual.
            with sock.makefile("r", encoding="utf-8", newline="\n") as socket_file:
                while self.running:
                    line = socket_file.readline()
                    if line == "":
                        break

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        if session is None:
                            self._send_raw(sock, {"type": "error", "message": "JSON inválido."})
                        else:
                            self._send_to_session(
                                session,
                                {"type": "error", "message": "JSON inválido."},
                            )
                        continue

                    message_type = message.get("type")

                    if session is None:
                        if message_type != "join":
                            self._send_raw(
                                sock,
                                {
                                    "type": "error",
                                    "message": "Debes hacer join antes de enviar mensajes.",
                                },
                            )
                            continue

                        session, close_after_join_error = self._handle_join(sock, message)
                        if close_after_join_error:
                            break
                        continue

                    if message_type == "chat":
                        self._handle_chat(session, message)
                        continue

                    if message_type == "history_request":
                        self._send_history(session)
                        continue

                    if message_type == "leave":
                        break

                    if message_type == "join":
                        self._send_to_session(
                            session,
                            {"type": "error", "message": "Ya estás dentro de la sala."},
                        )
                        continue

                    self._send_to_session(
                        session,
                        {"type": "error", "message": f"Tipo no reconocido: {message_type}"},
                    )

        except (ConnectionError, OSError):
            # La desconexión de un cliente no debe detener al servidor completo.
            pass
        finally:
            self._remove_client(sock)
            print(f"Cliente desconectado: {address}", flush=True)

    def serve_forever(self):
        """Abre el puerto y acepta conexiones hasta recibir una interrupción."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(MAX_CLIENTS)
        self.server_socket = server
        self.running = True

        print(
            f"Servidor empresarial escuchando en {self.host}:{self.port} "
            f"| BD: {self.database.database_path}",
            flush=True,
        )

        try:
            while self.running:
                client_sock, address = server.accept()
                print(f"Nueva conexión: {address}", flush=True)
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock, address),
                    daemon=True,
                )
                thread.start()
        finally:
            self.running = False
            try:
                server.close()
            except OSError:
                pass
