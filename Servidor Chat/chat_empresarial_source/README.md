# Chat empresarial — versión final cliente/servidor

Esta versión conserva la interfaz gráfica original y reemplaza el servidor temporal
en memoria por un servidor TCP persistente con SQLite.

## Comportamiento

- Máximo 10 usuarios conectados al mismo tiempo.
- Al entrar se solicita el nombre igual que en la interfaz original.
- Si `Ana` ya está conectada, la siguiente recibe `Ana2`, luego `Ana3`, etc.
- El color se mantiene determinado por el nombre definitivo usando la lógica original.
- Cada mensaje se guarda en SQLite **antes** de difundirse.
- El historial sobrevive al cierre/reinicio del servidor.
- El servidor envía automáticamente el historial al usuario justo después de `join_ok`.
- El botón **Recuperar historial** y `/history` siguen funcionando.

## Probar desde el código fuente

Servidor:

```bash
./run_server.sh
```

Cliente en el mismo computador:

```bash
./run_client.sh
```

Para clientes de otros computadores de la LAN, cambia `client_config.json`:

```json
{
  "host": "IP_DEL_SERVIDOR",
  "port": 5000
}
```

No se añadió ningún control visual para configurar la IP, precisamente para no
modificar la interfaz entregada.

## Instaladores Debian/Ubuntu

El paquete cliente instala un acceso en el menú de aplicaciones llamado
**Chat Empresarial**. Su configuración global queda en:

`/etc/chat-empresarial/client_config.json`

El paquete servidor instala y activa un servicio systemd. La base queda en:

`/var/lib/chat-empresarial/chat_history.db`

Comandos útiles del servidor:

```bash
sudo systemctl status chat-empresarial-server
sudo systemctl restart chat-empresarial-server
sudo journalctl -u chat-empresarial-server -f
```

## Importante antes de repartir el cliente

Como no se proporcionó todavía la IP o dominio definitivo del servidor, el
instalador viene con `127.0.0.1`. En los equipos cliente debe ponerse una sola vez
la IP real del servidor en `/etc/chat-empresarial/client_config.json`.
