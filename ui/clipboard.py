import secrets
from PySide6.QtCore import QMimeData, QObject, QTimer
from PySide6.QtWidgets import QApplication


class ClipboardGuard(QObject):
    """Очищає лише власний запис у буфері, не наступні копіювання користувача."""
    MIME = 'application/x-vault-copy-token'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.token = b''
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clear_owned)

    def copy(self, value):
        self.token = secrets.token_bytes(16)
        mime = QMimeData()
        mime.setText(value)
        mime.setData(self.MIME, self.token)
        QApplication.clipboard().setMimeData(mime)
        self.timer.start(20000)

    def clear_owned(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if self.token and mime and bytes(mime.data(self.MIME)) == self.token:
            clipboard.clear()
        self.timer.stop()
        self.token = b''


def clipboard_guard():
    app = QApplication.instance()
    if not hasattr(app, '_vault_clipboard_guard'):
        app._vault_clipboard_guard = ClipboardGuard(app)
        app.aboutToQuit.connect(app._vault_clipboard_guard.clear_owned)
    return app._vault_clipboard_guard
