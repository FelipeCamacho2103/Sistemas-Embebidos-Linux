# Arquitectura del chat empresarial

## Cliente

`client.py` carga `client_config.json` y crea la misma interfaz `ChatApp` que
existía en el proyecto entregado. `chat_client/network.py` mantiene un socket TCP
y recibe los JSON en un hilo secundario para no bloquear Tkinter.

## Servidor

`server.py` inicia `ChatServer`. Cada cliente aceptado se atiende en un hilo.
El servidor es la autoridad sobre:

- nombre definitivo (`Ana`, `Ana2`, ...);
- máximo de 10 usuarios conectados;
- hora del mensaje;
- ID global del mensaje;
- orden de difusión;
- historial persistente.

## Base de datos SQL

`chat_server/database.py` usa SQLite con la tabla:

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
```

El flujo de un mensaje es:

1. Cliente envía `{"type":"chat","text":"..."}`.
2. Servidor identifica el nombre a partir del socket.
3. Servidor inserta el mensaje en SQLite.
4. SQLite devuelve el ID permanente.
5. Servidor retransmite el mismo evento a todos los clientes.

Así nunca se considera confirmado un mensaje antes de quedar persistido.

## Historial al entrar

Después de `join_ok`, el servidor consulta SQLite y envía automáticamente un
evento `history`. Esto permite que la interfaz original muestre el historial sin
agregar botones ni campos nuevos.
