import time
from PySide6.QtCore import QObject, QEvent, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from browser_bridge.server import BridgeServer
from core.models import PasswordEntry
from core.origins import canonical_origin
from ui.clipboard import clipboard_guard
from ui.main_window import MainWindow
from ui.unlock_window import UnlockDialog


class SessionController(QObject):
    def __init__(self, repository, appearance, app):
        super().__init__(app)
        self.app = app
        self.repository = repository
        self.appearance = appearance
        self.vault = None
        self.window = None
        self.approved_origins = set()
        self.last_activity = time.time()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.check_idle)
        app.installEventFilter(self)
        self.bridge = BridgeServer(repository.path.parent, self.browser_request, self)
        self.request_busy = False

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel, QEvent.Type.TouchBegin):
            self.last_activity = time.time()
        return False

    def unlock(self):
        while True:
            dialog = UnlockDialog(self.repository, self.appearance)
            result = dialog.exec()
            if result == UnlockDialog.RESET_RESULT:
                dialog.deleteLater()
                continue
            if result != QDialog.DialogCode.Accepted:
                self.app.quit()
                return
            self.vault = dialog.vault
            dialog.vault = None
            dialog.deleteLater()
            break
        self.window = MainWindow(self.vault, self.appearance)
        self.window.lockRequested.connect(self.lock)
        self.window.closed.connect(self.app.quit)
        self.window.show()
        self.last_activity = time.time()
        self.timer.start()

    def check_idle(self):
        elapsed = time.time()-self.last_activity
        if self.vault and (elapsed < 0 or elapsed >= self.appearance.preferences.auto_lock_minutes*60):
            self.lock()

    def lock(self):
        if self.vault is None: return
        self.timer.stop()
        clipboard_guard().clear_owned()
        self.approved_origins.clear()
        if self.window:
            self.window.hide_password()
            for dialog in self.window.findChildren(QDialog):
                dialog.reject()
            self.window.username_value.clear()
            self.window.password_value.clear()
            self.window.entries.clear()
            self.window.hide()
            self.window.deleteLater()
            self.window = None
        self.vault.lock()
        self.vault = None
        QTimer.singleShot(0, self.unlock)

    def browser_request(self, message):
        if message.get('action') == 'status':
            return {'ok': True, 'locked': self.vault is None}
        if self.vault is None:
            return {'ok': False, 'error': 'Unlock the Vault desktop app first.'}
        if self.request_busy:
            return {'ok':False,'error':'Another browser request is waiting for approval.'}
        self.request_busy = True
        requested_vault = self.vault
        try:
            origin = canonical_origin(message.get('origin',''))
            action = message.get('action')
            if action not in ('list','fill','save'): raise ValueError('Unknown action')
            if origin not in self.approved_origins:
                answer=QMessageBox.question(self.window, self.appearance.tr('browser_access'), self.appearance.tr('browser_access_body', origin=origin), QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes or self.vault is not requested_vault:
                    return {'ok':False,'error':'Access was not approved.'}
                self.approved_origins.add(origin)
            if action == 'list':
                import json
                entries=[]
                for entry in self.vault.for_origin(origin):
                    if len(entry.id)>128: continue
                    candidate={'id':entry.id,'title':entry.title[:200],'username':entry.username[:512]}
                    if len(json.dumps(entries+[candidate],ensure_ascii=False).encode('utf-8'))>50000: break
                    entries.append(candidate)
                    if len(entries)>=50: break
                return {'ok':True,'entries':entries}
            if action == 'fill':
                entry=self.vault.get(message.get('id',''))
                if entry.url != origin: raise ValueError('Website does not match')
                self.last_activity=time.time()
                return {'ok':True,'username':entry.username,'password':entry.password,'origin':origin}
            username=message.get('username');password=message.get('password');title=message.get('title',origin)
            if not all(isinstance(value,str) for value in (username,password,title)) or not password or max(map(len,(username,password,title)))>4096:
                raise ValueError('Invalid entry')
            existing=next((entry for entry in self.vault.for_origin(origin) if entry.username==username),None)
            answer=QMessageBox.question(self.window,self.appearance.tr('browser_save'),self.appearance.tr('browser_save_body',origin=origin,username=username),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes or self.vault is not requested_vault:
                return {'ok':False,'error':'Save was cancelled.'}
            entry=PasswordEntry(title[:200],username,password,url=origin)
            if existing:
                entry.id=existing.id
                entry.app_package=existing.app_package
                entry.app_signature=existing.app_signature
            self.vault.save(entry)
            self.window.refresh_entries()
            self.last_activity=time.time()
            return {'ok':True}
        except (ValueError,KeyError,UnicodeError):
            return {'ok':False,'error':'Invalid request or website mismatch.'}
        except OSError:
            return {'ok':False,'error':'Could not save the vault.'}
        finally:
            self.request_busy=False

    def shutdown(self):
        self.timer.stop()
        if self.vault: self.vault.lock()
        clipboard_guard().clear_owned()
        self.bridge.close()
