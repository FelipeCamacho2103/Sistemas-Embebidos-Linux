import json


def encode_message(message):
    """
    Convierte un diccionario de Python a JSON y añade '\n'.

    Ese salto de línea funciona como delimitador entre mensajes TCP.
    """
    text = json.dumps(message, ensure_ascii=False)
    return (text + "\n").encode("utf-8")


def decode_message(line):
    """
    Convierte una línea JSON recibida desde el servidor en un diccionario.
    """
    return json.loads(line)
