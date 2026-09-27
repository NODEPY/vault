import json
import os
import secrets
import socketserver
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot
from browser_bridge.protocol import read_message, write_message


class Dispatcher(QObject):
    requested = Signal(object)

    def __init__(self, handler, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.requested.connect(self.dispatch)

    @Slot(object)
    def dispatch(self, job):
        if job['cancelled'].is_set(): return
        try:
            job['result'] = self.handler(job['message'])
        except Exception:
            # Never log request bodies or credential values.
            job['result'] = {'ok': False, 'error': 'The request could not be completed.'}
        finally:
            job['done'].set()


class BridgeServer:
    def __init__(self, directory, handler, parent=None):
        self.path = Path(directory)/'browser-session.json'
        self.token = secrets.token_hex(32)
        self.dispatcher = Dispatcher(handler, parent)
        owner = self
        slots = threading.BoundedSemaphore(8)
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                if not slots.acquire(blocking=False): return
                try:
                    self.connection.settimeout(3)
                    envelope = read_message(self.rfile)
                    if not envelope or not isinstance(envelope.get('token'), str) or not secrets.compare_digest(envelope['token'], owner.token):
                        return
                    if not isinstance(envelope.get('message'), dict): return
                    job = {'message':envelope['message'], 'done':threading.Event(), 'cancelled':threading.Event()}
                    owner.dispatcher.requested.emit(job)
                    if not job['done'].wait(60):
                        job['cancelled'].set()
                        response = {'ok':False,'error':'Desktop approval timed out.'}
                    else: response = job['result']
                    write_message(self.wfile, response)
                except (OSError, ValueError, EOFError): pass
                finally: slots.release()
        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True
            request_queue_size = 8
        self.server = Server(('127.0.0.1',0), Handler)
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        fd = os.open(self.path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
        with os.fdopen(fd,'w') as file:
            json.dump({'port':self.server.server_address[1],'token':self.token},file)
        if os.name != 'nt': self.path.chmod(0o600)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.path.unlink(missing_ok=True)
