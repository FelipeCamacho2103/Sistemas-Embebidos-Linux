# Sistema domótico distribuido

Sistema modular de adquisición y procesamiento de información sensorial orientado al seguimiento de rutinas y al apoyo de personas que viven solas.

## Arquitectura

- Tres nodos ESP32 con firmware universal.
- Milk-V Duo S como unidad central de procesamiento.
- Comunicación mediante Wi-Fi y MQTT.
- Adquisición y transmisión independientes.

## Hardware

- ESP32-WROOM-32.
- Sensor PIR HC-SR501.
- Sensor acústico KY-038.
- Contacto magnético de puerta.
- Milk-V Duo S.

## Firmware

- Lenguaje C.
- Framework ESP-IDF.
- PlatformIO.
- Visual Studio Code.
- Interrupciones GPIO, marcas temporales y colas de eventos.

## Metodología

Desarrollo incremental y modular, con pruebas independientes de los componentes y desarrollo paralelo de funcionalidades.

## Control de versiones

- Git.
- Ramas de funcionalidad.
- Conventional Commits.
- Semantic Versioning.

## Estado del proyecto

Configuración inicial del entorno de desarrollo.
