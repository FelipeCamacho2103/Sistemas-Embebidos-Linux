import queue
import socket
import threading

from .protocol import decode_message, encode_message


class NetworkClient:
    """
    Maneja exclusivamente la comunicación TCP.

    La interfaz gráfica no lee directamente del socket.
    Los mensajes recibidos se colocan en incoming_queue.
    """

    def __init__(self, host, port, incoming_queue):
        self.host = host
        self.port = port
        self.incoming_queue = incoming_queue

        self.sock = None
        self.reader_thread = None
        self.running = False
        self.send_lock = threading.Lock()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        self.running = True

        self.reader_thread = threading.Thread(
            target=self._receive_loop,
            daemon=True,
        )
        self.reader_thread.start()

    def send(self, message):
        if not self.running or self.sock is None:
            raise ConnectionError("No existe una conexión activa con el servidor.")

        data = encode_message(message)

        # Varios eventos de la GUI podrían intentar enviar datos casi al mismo tiempo.
        # El lock evita mezclar bytes de dos mensajes distintos.
        with self.send_lock:
            self.sock.sendall(data)

    def close(self):
        self.running = False

        if self.sock is None:
            return

        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.sock.close()
        except OSError:
            pass

        self.sock = None

    def _receive_loop(self):
        """
        Se ejecuta en un hilo secundario.

        makefile() permite leer el socket línea por línea. Como el protocolo
        termina cada JSON con '\n', cada readline() corresponde a un mensaje.
        """
        try:
            with self.sock.makefile(
                mode="r",
                encoding="utf-8",
                newline="\n",
            ) as socket_file:
                while self.running:
                    line = socket_file.readline()

                    if line == "":
                        raise ConnectionError("El servidor cerró la conexión.")

                    line = line.strip()

                    if not line:
                        continue

                    try:
                        message = decode_message(line)
                    except ValueError as exc:
                        self.incoming_queue.put(
                            {
                                "type": "local_error",
                                "message": f"JSON inválido recibido: {exc}",
                            }
                        )
                        continue

                    self.incoming_queue.put(message)

        except (ConnectionError, OSError) as exc:
            if self.running:
                self.incoming_queue.put(
                    {
                        "type": "connection_lost",
                        "message": str(exc),
                    }
                )
        finally:
            self.running = False
