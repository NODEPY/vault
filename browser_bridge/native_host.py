"""Chrome stdio host. It never opens or decrypts the vault file itself."""
import json
import os
import secrets
import socket
import sys

from browser_bridge.config import EXTENSION_ID
from browser_bridge.paths import data_directory
from browser_bridge.protocol import read_message, write_message


def relay(message, directory=None):
    directory = directory or data_directory()
    descriptor = json.loads((directory/'browser-session.json').read_text())
    if not isinstance(descriptor.get('port'), int) or not 1 <= descriptor['port'] <= 65535:
        raise ValueError('Invalid session')
    with socket.create_connection(('127.0.0.1', descriptor['port']), timeout=2) as connection:
        connection.settimeout(65)
        stream = connection.makefile('rwb')
        write_message(stream, {'token': descriptor['token'], 'message': message})
        response = read_message(stream)
        if response is None: raise ValueError('No response')
        return response


def run():
    directory = data_directory()
    allowed = [EXTENSION_ID]
    try:
        allowed = json.loads((directory/'chrome-registration.json').read_text())['extension_ids']
    except (OSError, ValueError, KeyError): pass
    origin = sys.argv[1] if len(sys.argv)>1 else ''
    if origin not in ['chrome-extension://' + value + '/' for value in allowed]: return 1
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    try:
        request = read_message(sys.stdin.buffer)
        if request is None: return 0
        response = relay(request, directory)
    except (OSError, EOFError, ValueError, KeyError):
        response = {'ok': False, 'error': 'Open and unlock the Vault desktop app.'}
    write_message(sys.stdout.buffer, response)
    return 0
