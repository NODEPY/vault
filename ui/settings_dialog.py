from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLabel, QVBoxLayout,
)
from core.settings import Preferences
from ui.themes import LANGUAGES, THEMES
from PySide6.QtGui import QIcon, QPixmap, QColor


class SettingsDialog(QDialog):
    def __init__(self, appearance, parent=None, onboarding=False):
        super().__init__(parent)
        self.appearance = appearance
        self.original = appearance.preferences
        self.onboarding = onboarding
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(20)
        self.title = QLabel()
        self.title.setObjectName("title")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("subtitle")
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.setSpacing(16)
        self.language_label, self.theme_label = QLabel(), QLabel()
        self.language_combo = QComboBox()
        for code, name in LANGUAGES:
            self.language_combo.addItem(name, code)
        self.language_combo.setCurrentIndex(self.language_combo.findData(self.original.language))
        self.theme_combo = QComboBox()
        for code, colors in THEMES.items():
            swatch = QPixmap(18, 18)
            swatch.fill(QColor(colors["accent"]))
            self.theme_combo.addItem(QIcon(swatch), colors["name"], code)
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(self.original.theme))
        form.addRow(self.language_label, self.language_combo)
        form.addRow(self.theme_label, self.theme_combo)
        self.lock_label = QLabel()
        self.lock_combo = QComboBox()
        for minutes in (1, 5, 15, 30): self.lock_combo.addItem(str(minutes), minutes)
        self.lock_combo.setCurrentIndex(self.lock_combo.findData(self.original.auto_lock_minutes))
        form.addRow(self.lock_label, self.lock_combo)
        layout.addLayout(form)
        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.language_combo.currentIndexChanged.connect(self.preview)
        self.theme_combo.currentIndexChanged.connect(self.preview)
        self.retranslate()

    def selection(self):
        return Preferences(self.language_combo.currentData(), self.theme_combo.currentData(), self.lock_combo.currentData())

    def preview(self, _index=None):
        self.error_label.clear()
        self.appearance.apply(self.selection())
        self.retranslate()

    def retranslate(self):
        tr = self.appearance.tr
        self.setWindowTitle(tr("welcome" if self.onboarding else "settings"))
        self.title.setText(self.windowTitle())
        self.subtitle.setText(tr("welcome_hint" if self.onboarding else "settings_hint"))
        self.language_label.setText(tr("language"))
        self.theme_label.setText(tr("theme"))
        self.lock_label.setText(tr("auto_lock"))
        for index in range(self.lock_combo.count()):
            self.lock_combo.setItemText(index, tr("minutes", count=self.lock_combo.itemData(index)))

        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("continue" if self.onboarding else "save"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("exit" if self.onboarding else "cancel"))
        cancel = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel.setObjectName("secondary")
        cancel.style().unpolish(cancel)
        cancel.style().polish(cancel)

    def save_settings(self):
        try:
            self.appearance.save(self.selection())
        except OSError:
            self.error_label.setText(self.appearance.tr("settings_error"))
            return
        self.accept()

    def reject(self):
        self.appearance.apply(self.original)
        super().reject()
