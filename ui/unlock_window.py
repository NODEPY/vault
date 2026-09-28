from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

from core.security import VaultUnlockError
from core.vault import Vault
from storage.repository import VaultFormatError, VaultRepository
from ui.appearance import Appearance
from ui.reset_dialog import ResetDialog
from ui.settings_dialog import SettingsDialog


class UnlockDialog(QDialog):
    RESET_RESULT = 2

    def __init__(self, repository: VaultRepository, appearance=None):
        super().__init__()
        self.repository = repository
        self.appearance = appearance or Appearance()
        self.vault = None
        self.creating = not repository.path.exists()
        self.setMinimumWidth(490)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(18)
        self.title = QLabel()
        self.title.setObjectName("title")
        layout.addWidget(self.title)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setObjectName("subtitle")
        layout.addWidget(self.description)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.setSpacing(14)
        self.password_label, self.confirm_label = QLabel(), QLabel()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(self.password_label, self.password_input)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.creating:
            form.addRow(self.confirm_label, self.confirm_input)
        else:
            self.confirm_input.hide()
            self.confirm_label.hide()
        layout.addLayout(form)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setObjectName("error")
        layout.addWidget(self.error_label)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.unlock)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        footer = QHBoxLayout()
        self.settings_button = QPushButton()
        self.settings_button.setObjectName("secondary")
        self.settings_button.clicked.connect(self.open_settings)
        footer.addWidget(self.settings_button)
        self.forgot_button = QPushButton()
        self.forgot_button.setObjectName("secondary")
        self.forgot_button.setVisible(not self.creating)
        self.forgot_button.clicked.connect(self.reset_vault)
        footer.addWidget(self.forgot_button)
        layout.addLayout(footer)
        self.retranslate()
        self.password_input.setFocus()

    def retranslate(self):
        tr = self.appearance.tr
        self.setWindowTitle(tr("master_window"))
        self.title.setText(tr("create_title" if self.creating else "unlock_title"))
        self.description.setText(tr("create_hint" if self.creating else "unlock_hint"))
        self.password_label.setText(tr("master"))
        self.confirm_label.setText(tr("repeat"))
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("create" if self.creating else "unlock"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("exit"))
        self.settings_button.setText(tr("settings"))
        self.forgot_button.setText(tr("forgot"))

    def open_settings(self):
        dialog = SettingsDialog(self.appearance, self)
        dialog.exec()
        dialog.deleteLater()
        self.error_label.clear()
        self.retranslate()

    def reset_vault(self):
        if self.creating:
            return
        dialog = ResetDialog(self.appearance, self)
        result = dialog.exec()
        dialog.deleteLater()
        if result != QDialog.DialogCode.Accepted:
            return
        try:
            self.repository.delete_all()
        except OSError:
            self.error_label.setText(self.appearance.tr("reset_error"))
            return
        self.password_input.clear()
        self.confirm_input.clear()
        self.done(self.RESET_RESULT)

    def unlock(self):
        tr = self.appearance.tr
        password = self.password_input.text()
        self.error_label.clear()
        if not password:
            self.error_label.setText(tr("enter_master"))
            return
        if self.creating:
            if len(password) < 12:
                self.error_label.setText(tr("short_master"))
                return
            if password != self.confirm_input.text():
                self.error_label.setText(tr("mismatch"))
                return
        try:
            if self.creating:
                if self.repository.path.exists():
                    self.error_label.setText(tr("vault_exists"))
                    return
                self.repository.save([], password)
                entries = []
            else:
                entries = self.repository.load(password)
        except VaultUnlockError:
            self.error_label.setText(tr("unlock_error"))
            self.password_input.clear()
            self.password_input.setFocus()
            return
        except VaultFormatError:
            self.error_label.setText(tr("format_error"))
            return
        except OSError:
            self.error_label.setText(tr("file_error"))
            return
        self.vault = Vault(self.repository, password, entries)
        self.password_input.clear()
        self.confirm_input.clear()
        self.accept()
