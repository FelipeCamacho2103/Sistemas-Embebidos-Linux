# Servidor Chat

Proyecto de servidor de chat desarrollado para Sistemas Linux Embebidos.

Integrantes:

-Valeria Corredor

-Sergio González

-Felipe Camacho

Para conectarse al servidor, es necesario activarlo en un dispositivo con una distro basada en debian y utilizar 
el cliente debian o windows de acuerdo al SO. Los clientes deben estar dentro de su alcance de red y configurar, la primera vez, la dirección IP del servidor y el puerto con el servicio TCP. 
Características
- Hasta 10 usuarios conectados simultáneamente.
- Interfaz gráfica de escritorio con lista de participantes en línea.
- Nombres únicos asignados automáticamente: si Ana ya está en uso, se asigna Ana2, Ana3, etc.
- Mensajes con autor, hora y orden global determinados por el servidor.
- Historial almacenado en SQLite, persistente entre reinicios.
- Recuperación automática del historial al ingresar, además del botón Recuperar historial y el comando /history.
- Cliente para Linux (paquete .deb) y ejecutable para Windows (archivo .exe).
- Protocolo de intercambio: JSON codificado en UTF-8, un mensaje por línea sobre TCP.
1. Archivos disponibles
ChatEmpresarial_Servidor_1.0.0_all.deb	Instalador del servidor para sistemas Debian/Ubuntu.
ChatEmpresarial_Cliente_1.0.0_all.deb	Instalador del cliente para Debian/Ubuntu.
ChatEmpresarialCliente_Windows_x64.exe	Ejecutable del cliente para Windows de 64 bits.
chat_empresarial_source/	Código fuente, scripts, pruebas y documentación técnica.
Chat_Empresarial_Descripcion_Arquitectura_Verificacion.docx	Documento de descripción, arquitectura y verificación del proyecto.


Importante: para que otros equipos puedan usar el chat, primero debe estar ejecutándose el servidor y los clientes deben apuntar a su IP real. La dirección 127.0.0.1 solo sirve cuando cliente y servidor se ejecutan en el mismo equipo.

2. Instalación del servidor (Debian/Ubuntu)
Paso 1. Descargar el instalador
Descargue ChatEmpresarial_Servidor_1.0.0_all.deb desde esta carpeta del repositorio y abra una terminal en el directorio donde lo guardaste.
Paso 2. Instalar el paquete
```bash
sudo apt install ./ChatEmpresarial_Servidor_1.0.0_all.deb
```
El paquete instala un servicio de systemd llamado chat-empresarial-server.
Paso 3. Comprobar que está ejecutándose
```bash
sudo systemctl status chat-empresarial-server
```

Si necesita iniciarlo manualmente:
```bash
sudo systemctl start chat-empresarial-server
```
Para reiniciarlo después de cambios:
```bash
sudo systemctl restart chat-empresarial-server
```
Para ver los registros en tiempo real:
```bash
sudo journalctl -u chat-empresarial-server -f
```
La base de datos del servidor instalado se ubica en:
/var/lib/chat-empresarial/chat_history.db
Paso 4. Obtener la IP del servidor
hostname -I
Identifique la dirección IPv4 correspondiente a la red local en la que se encuentran los clientes. Por ejemplo, 192.168.1.50.

Puerto predeterminado: 5000/TCP.

Si el equipo usa ufw, permita el acceso desde su red local. Como ejemplo, para una LAN 192.168.1.0/24:
sudo ufw allow from 192.168.1.0/24 to any port 5000 proto tcp
3. Instalar y utilizar el cliente en Linux
Paso 1. Instalar el paquete
Descargue ChatEmpresarial_Cliente_1.0.0_all.deb y ejecute:
```bash
sudo apt install ./ChatEmpresarial_Cliente_1.0.0_all.deb
```
El paquete agrega una aplicación al menú del sistema con el nombre Chat Empresarial.
Paso 2. Configurar la conexión
En una instalación mediante .deb, la configuración del cliente se guarda en:
/etc/chat-empresarial/client_config.json
Edítela con permisos administrativos:
```bash
sudo nano /etc/chat-empresarial/client_config.json
```
Use la IP real del servidor:
{
  "host": "xxx.xxx.xxx.xxx",
  "port": 5000
}
Guarde el archivo y abra Chat Empresarial desde el menú de aplicaciones.
4. Utilizar el cliente en Windows
  1. Descargue ChatEmpresarialCliente_Windows_x64.exe.
  2. Ejecute el archivo en Windows de 64 bits.
  3. Compruebe que el servidor esté en ejecución y sea accesible desde la misma red.

5. Ejecutar desde el código fuente (Linux)
Sirve para desarrollar, depurar o probar el sistema sin instalar paquetes.
Requisitos
- Python 3.
- Tkinter disponible en el sistema para la interfaz gráfica.
- Acceso TCP entre el cliente y el servidor.
En Debian/Ubuntu, instala Python y Tkinter si todavía no están disponibles:
```bash
sudo apt update
sudo apt install python3 python3-tk
```
Abra una terminal en chat_empresarial_source/.
Iniciar el servidor
```bash
python3 server.py
```
El servidor usa por defecto la interfaz 0.0.0.0, el puerto 5000 y la base de datos data/chat_history.db dentro de la carpeta del proyecto.

También puede iniciarlo usando el script incluido:
```bash
sh run_server.sh
```
Para configurar explícitamente los parámetros:
python3 server.py --host 0.0.0.0 --port 5000 --database ./data/chat_history.db
0.0.0.0 significa que el servidor escucha en todas las interfaces IPv4 disponibles; los clientes deben conectarse a una IP concreta del equipo, no a 0.0.0.0.

Iniciar el cliente
En otra terminal, dentro de chat_empresarial_source/:
```bash
python3 client.py --host 127.0.0.1 --port 5000
```
Use 127.0.0.1 solo para pruebas locales. Desde otro equipo de la LAN:
```bash
python3 client.py --host 192.168.1.50 --port 5000
```
También puede editar chat_empresarial_source/client_config.json con la IP del servidor y ejecutar:
```bash
sh run_client.sh
```
Nota: el archivo de configuración global /etc/chat-empresarial/client_config.json, si existe, tiene prioridad sobre el archivo local. Los argumentos --host y --port permiten reemplazar ambos valores al ejecutar el cliente desde Python.
6. ¿Cómo utilizar la sala de chat?
1. Inicie el servidor y después abre uno o varios clientes.
2. Cuando aparezca la ventana Entrar a la sala, escriba su nombre, de hasta 24 caracteres, y pulse Entrar.
3. Si ya existe un usuario con ese nombre, el servidor asignará automáticamente otro disponible, por ejemplo Ana2.
4. Escriba un mensaje en el campo inferior y presione Enter o el botón Enviar.
5. La columna En línea mostrará los usuarios conectados.
6. Pulse Recuperar historial, o escriba /history, para solicitar los mensajes guardados.
7. Cierre la ventana del cliente para salir de la sala.
Los mensajes tienen un máximo de 1000 caracteres. No se muestran como enviados hasta que el servidor los procesa y los retransmite; por eso todos los clientes utilizan el orden asignado por el servidor.
Ejemplo de funcionamiento
Equipo Linux / servidor — 192.168.1.50:5000
             |
             +---- Cliente Windows: Ana
             |
             +---- Cliente Linux: Carlos
             |
             +---- Cliente Linux: Ana2

[10:15:02] Ana: Hola a todos
[10:15:07] Carlos: Buen día
[10:15:12] Ana2: ¿Cómo están?
Los mensajes son almacenados en SQLite y podrán recuperarse incluso después de reiniciar el servidor, siempre que se conserve el archivo de base de datos.
7. Diagnóstico de problemas frecuentes
Problema	Posible causa y solución
No se pudo conectar:	Revise que el servicio del servidor esté activo, que la IP sea correcta y que el puerto 5000/TCP esté permitido en el firewall.
El cliente intenta conectar a 127.0.0.1:	Cambie host por la IP del servidor; 127.0.0.1 apunta al mismo computador donde corre el cliente.
La sala está llena:	El servidor admite máximo 10 usuarios. Espere a que uno se desconecte.
El nombre cambia de Ana a Ana2_:	Otro usuario ya ocupa Ana; es el comportamiento previsto para impedir nombres duplicados.
No aparece el historial:	Compruebe el servicio y los registros. Verifique que la base de datos sea accesible para el proceso del servidor.
Se pierde la conexión:	Compruebe conectividad LAN, cambios de IP, suspensión del equipo o reinicios del servidor. Reabra el cliente después de restablecer el servicio.
Falla la interfaz gráfica en Linux:	Compruebe que python3-tk esté instalado y que haya una sesión gráfica disponible.


Para diagnosticar una instalación de servidor en Debian/Ubuntu:
```bash
sudo systemctl status chat-empresarial-server
sudo journalctl -u chat-empresarial-server -n 50 --no-pager
```
En un cliente Linux puede comprobar que el puerto TCP está accesible:
```bash
nc -vz 192.168.1.50 5000
```
