from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout


class ResetDialog(QDialog):
    """Підтвердження скидання. Сам діалог нічого не видаляє."""
    def __init__(self, appearance, parent=None):
        super().__init__(parent)
        tr = appearance.tr
        self.token = tr("reset_token")
        self.setWindowTitle(tr("reset_title"))
        self.setMinimumWidth(510)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)
        title = QLabel(tr("reset_title"))
        title.setObjectName("title")
        layout.addWidget(title)
        body = QLabel(tr("reset_body"))
        body.setWordWrap(True)
        layout.addWidget(body)
        layout.addWidget(QLabel(tr("reset_instruction")))
        self.confirm_input = QLineEdit()
        layout.addWidget(self.confirm_input)
        buttons = QHBoxLayout()
        cancel = QPushButton(tr("cancel"))
        cancel.setObjectName("secondary")
        cancel.setDefault(True)
        cancel.clicked.connect(self.reject)
        self.delete_button = QPushButton(tr("delete_all"))
        self.delete_button.setObjectName("danger")
        self.delete_button.setAutoDefault(False)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.confirm)
        self.confirm_input.textChanged.connect(self.update_confirmation)
        buttons.addWidget(cancel)
        buttons.addWidget(self.delete_button)
        layout.addLayout(buttons)

    def update_confirmation(self, text):
        self.delete_button.setEnabled(text == self.token)

    def confirm(self):
        if self.confirm_input.text() == self.token:
            self.accept()
