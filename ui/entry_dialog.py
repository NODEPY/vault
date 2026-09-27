from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from core.models import PasswordEntry
from core.origins import canonical_origin
from ui.appearance import Appearance
from ui.generator_dialog import GeneratorDialog
from ui.icons import icon


class EntryDialog(QDialog):
    def __init__(self, parent=None, entry=None, appearance=None):
        super().__init__(parent)

        self._entry = entry
        self.appearance = appearance or Appearance()
        tr = self.appearance.tr

        self.setWindowTitle(
            tr("edit_entry") if entry else tr("new_entry")
        )
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        heading = QLabel(
            tr("edit_entry") if entry else tr("new_entry")
        )
        heading.setObjectName("title")
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(12)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(tr("service_example"))
        self.title_input.setMaxLength(200)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(tr("username_hint"))

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(tr("password"))
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        form.addRow(tr("service"), self.title_input)
        form.addRow(tr("website"), self.url_input)
        form.addRow(tr("username"), self.username_input)
        password_row = QHBoxLayout()
        password_row.addWidget(self.password_input, 1)
        self.generate_button = QPushButton(tr("generator"))
        self.generate_button.setObjectName("secondary")
        self.generate_button.setIcon(icon("dice", self.appearance.colors["fg"]))
        self.generate_button.clicked.connect(self.open_generator)
        password_row.addWidget(self.generate_button)
        form.addRow(tr("password"), password_row)

        layout.addLayout(form)

        show_password = QCheckBox(tr("show_password"))
        show_password.toggled.connect(self.toggle_password)
        layout.addWidget(show_password)

        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.button(
            QDialogButtonBox.StandardButton.Save
        ).setText(tr("save"))

        buttons.button(
            QDialogButtonBox.StandardButton.Cancel
        ).setText(tr("cancel"))

        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel.setObjectName("secondary")
        cancel.style().unpolish(cancel)
        cancel.style().polish(cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if entry is not None:
            self.title_input.setText(entry.title)
            self.url_input.setText(entry.url)
            self.username_input.setText(entry.username)
            self.password_input.setText(entry.password)

        self.title_input.setFocus()

    def toggle_password(self, visible):
        mode = (
            QLineEdit.EchoMode.Normal
            if visible
            else QLineEdit.EchoMode.Password
        )
        self.password_input.setEchoMode(mode)

    def validate_and_accept(self):
        if not self.title_input.text().strip():
            self.error_label.setText(self.appearance.tr("enter_title"))
            self.title_input.setFocus()
            return

        if not self.password_input.text():
            self.error_label.setText(self.appearance.tr("enter_password"))
            self.password_input.setFocus()
            return

        if self.url_input.text().strip():
            try:
                canonical_origin(self.url_input.text())
            except (ValueError, UnicodeError):
                self.error_label.setText(self.appearance.tr("invalid_website"))
                return
        self.accept()

    def get_entry(self) -> PasswordEntry:
        values = {
            "title": self.title_input.text().strip(),
            "username": self.username_input.text().strip(),
            # Пробіли можуть бути частиною пароля.
            "password": self.password_input.text(),
            "url": canonical_origin(self.url_input.text()) if self.url_input.text().strip() else "",
        }

        if self._entry is not None:
            return PasswordEntry(
                id=self._entry.id,
                app_package=self._entry.app_package,
                app_signature=self._entry.app_signature,
                **values,
            )

        return PasswordEntry(**values)

    def open_generator(self):
        dialog = GeneratorDialog(self.appearance, self, allow_use=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.password_input.setText(dialog.value())
        dialog.deleteLater()
