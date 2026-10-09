# Protocolo cliente-servidor

El transporte es TCP. Cada mensaje de aplicación es JSON UTF-8 terminado en `\n`.
El salto de línea es el delimitador de mensajes sobre el flujo TCP.

## 1. Entrada

Cliente -> servidor:

```json
{"type":"join","requested_name":"Ana"}
```

Servidor -> cliente:

```json
{"type":"join_ok","assigned_name":"Ana"}
```

Si el nombre está ocupado, el servidor asigna `Ana2`, `Ana3`, etc. El servidor,
no el cliente, mantiene la lista de nombres ocupados.

## 2. Presencia (ampliación para la interfaz)

Servidor -> todos los clientes, cada vez que entra o sale alguien:

```json
{
  "type":"presence",
  "count":3,
  "users":["Ana","Ana2","Luis"]
}
```

Este evento permite mostrar el número y la lista de usuarios conectados. Es una
mejora de presentación: si el servidor real todavía no la implementa, mensajes,
historial y conexión siguen funcionando; únicamente no se actualizará la barra
lateral de presencia.

## 3. Mensajes

Cliente -> servidor:

```json
{"type":"chat","text":"Hola a todos"}
```

El cliente no dibuja todavía el mensaje. El servidor determina el usuario a
partir del socket, asigna ID y hora, persiste y retransmite:

```json
{
  "id":17,
  "type":"message",
  "sender":"Ana",
  "text":"Hola a todos",
  "timestamp":"2026-09-29 11:42:03"
}
```

El ID es la referencia de orden. La hora y el nombre definitivo son autoridad
del servidor.

## 4. Historial

Cliente -> servidor:

```json
{"type":"history_request"}
```

Servidor -> cliente:

```json
{
  "type":"history",
  "messages":[
    {"id":15,"sender":"Ana","text":"Hola","timestamp":"2026-09-29 11:40:10"},
    {"id":16,"sender":"Luis","text":"Buenas","timestamp":"2026-09-29 11:40:15"}
  ]
}
```

En el servidor definitivo, el historial debería venir de la base de datos y
ordenarse por `id ASC`.

## 5. Salida y auxiliares

Cliente -> servidor:

```json
{"type":"leave"}
```

Servidor -> cliente:

```json
{"type":"system","message":"Luis entró a la sala."}
```

```json
{"type":"error","message":"Mensaje demasiado largo."}
```

## Contrato mínimo que debe respetar el servidor real

- máximo de conexiones definido por el proyecto;
- nombre definitivo asignado en el servidor;
- no confiar en un `sender` enviado por el cliente;
- ID y timestamp generados en el servidor;
- persistir antes de retransmitir;
- historial ordenado por ID;
- liberar nombres al cerrar el socket;
- serializar el orden global de mensajes;
- para la lista lateral, emitir `presence` al entrar/salir.
