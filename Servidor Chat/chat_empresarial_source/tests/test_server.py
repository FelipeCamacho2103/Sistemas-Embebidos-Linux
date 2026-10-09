"""Pruebas de integración básicas del servidor sin abrir la interfaz Tkinter."""

import json
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 54321
DATABASE = Path(tempfile.mkdtemp()) / "chat_test.db"


def start_server():
    """Inicia el servidor real con una base temporal para no tocar datos de producción."""
    process = subprocess.Popen(
        [
            sys.executable,
            "server.py",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
            "--database",
            str(DATABASE),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            probe = socket.create_connection(("127.0.0.1", PORT), timeout=0.2)
            probe.close()
            return process
        except OSError:
            time.sleep(0.05)

    raise RuntimeError("El servidor no inició dentro del tiempo de prueba.")


def stop_server(process):
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


class TestClient:
    """Cliente TCP mínimo para comprobar el protocolo del servidor."""

    def __init__(self):
        self.sock = socket.create_connection(("127.0.0.1", PORT), timeout=2)
        self.sock.settimeout(2)
        self.file = self.sock.makefile("r", encoding="utf-8", newline="\n")

    def send(self, message):
        payload = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
        self.sock.sendall(payload)

    def receive(self):
        return json.loads(self.file.readline())

    def wait_for(self, event_type):
        deadline = time.time() + 3
        while time.time() < deadline:
            event = self.receive()
            if event.get("type") == event_type:
                return event
        raise AssertionError(f"No llegó el evento {event_type}")

    def close(self):
        try:
            self.send({"type": "leave"})
        except OSError:
            pass
        self.file.close()
        self.sock.close()


def main():
    # 1) Nombres repetidos + primer mensaje persistente.
    server = start_server()
    try:
        ana = TestClient()
        ana.send({"type": "join", "requested_name": "Ana"})
        assert ana.wait_for("join_ok")["assigned_name"] == "Ana"
        assert ana.wait_for("history")["messages"] == []

        ana2 = TestClient()
        ana2.send({"type": "join", "requested_name": "Ana"})
        assert ana2.wait_for("join_ok")["assigned_name"] == "Ana2"
        assert ana2.wait_for("history")["messages"] == []

        ana.send({"type": "chat", "text": "mensaje persistente"})
        assert ana.wait_for("message")["id"] == 1
        assert ana2.wait_for("message")["id"] == 1

        # 2) Dos clientes escribiendo casi a la vez siguen obteniendo IDs únicos.
        first = threading.Thread(
            target=lambda: ana.send({"type": "chat", "text": "mensaje A"})
        )
        second = threading.Thread(
            target=lambda: ana2.send({"type": "chat", "text": "mensaje B"})
        )
        first.start()
        second.start()
        first.join()
        second.join()

        ids = []
        while len(ids) < 2:
            event = ana.receive()
            if event.get("type") == "message":
                ids.append(event["id"])
        assert sorted(ids) == [2, 3]

        ana.close()
        ana2.close()
    finally:
        stop_server(server)

    # 3) Reiniciamos el servidor y comprobamos que SQLite conserva los 3 mensajes.
    server = start_server()
    try:
        client = TestClient()
        client.send({"type": "join", "requested_name": "Carlos"})
        client.wait_for("join_ok")
        history = client.wait_for("history")["messages"]
        assert [message["id"] for message in history] == [1, 2, 3]
        client.close()
    finally:
        stop_server(server)

    print("Pruebas completadas correctamente.")


if __name__ == "__main__":
    main()
