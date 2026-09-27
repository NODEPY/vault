from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QSlider, QSpinBox, QVBoxLayout,
)
from core.generator import generate_password, generate_passphrase
from ui.clipboard import clipboard_guard
from ui.icons import icon


class GeneratorDialog(QDialog):
    def __init__(self, appearance, parent=None, allow_use=False):
        super().__init__(parent)
        self.appearance = appearance
        tr = appearance.tr
        self.setWindowTitle(tr('generator'))
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)
        title = QLabel(tr('generator'))
        title.setObjectName('title')
        layout.addWidget(title)
        subtitle = QLabel(tr('generator_hint'))
        subtitle.setObjectName('subtitle')
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        self.mode = QComboBox()
        self.mode.addItem(tr('random_password'), 'password')
        self.mode.addItem(tr('passphrase'), 'phrase')
        layout.addWidget(self.mode)
        self.output = QPlainTextEdit()
        self.output.setObjectName('generated')
        self.output.setReadOnly(True)
        self.output.setFixedHeight(112)
        self.output.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        layout.addWidget(self.output)
        options = QHBoxLayout()
        self.length_label = QLabel()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.length = QSpinBox()
        self.length.setMinimumWidth(70)
        options.addWidget(self.length_label)
        options.addWidget(self.slider, 1)
        options.addWidget(self.length)
        layout.addLayout(options)
        self.symbols = QCheckBox(tr('symbols'))
        self.symbols.setChecked(True)
        layout.addWidget(self.symbols)
        self.explanation = QLabel()
        self.explanation.setWordWrap(True)
        self.explanation.setObjectName('hint')
        layout.addWidget(self.explanation)
        actions = QHBoxLayout()
        self.regenerate_button = QPushButton(tr('regenerate'))
        self.regenerate_button.setObjectName('secondary')
        self.regenerate_button.setIcon(icon('refresh', appearance.colors['fg']))
        self.copy_button = QPushButton(tr('copy'))
        self.copy_button.setObjectName('secondary')
        actions.addWidget(self.regenerate_button)
        actions.addStretch()
        actions.addWidget(self.copy_button)
        if allow_use:
            self.use_button = QPushButton(tr('use_password'))
            self.use_button.clicked.connect(self.accept)
            actions.addWidget(self.use_button)
        else:
            close_button = QPushButton(tr('close'))
            close_button.clicked.connect(self.reject)
            actions.addWidget(close_button)
        layout.addLayout(actions)
        self.status = QLabel(tr('generator_privacy'))
        self.status.setObjectName('hint')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.slider.valueChanged.connect(self.length.setValue)
        self.length.valueChanged.connect(self.slider.setValue)
        self.length.valueChanged.connect(self.regenerate)
        self.symbols.toggled.connect(self.regenerate)
        self.regenerate_button.clicked.connect(self.regenerate)
        self.copy_button.clicked.connect(self.copy_value)
        self.mode_changed()

    def mode_changed(self, _index=None):
        phrase = self.mode.currentData() == 'phrase'
        self.length.blockSignals(True)
        self.slider.blockSignals(True)
        for control in (self.length, self.slider):
            control.setRange(6 if phrase else 12, 10 if phrase else 64)
            control.setValue(8 if phrase else 20)
        self.length.blockSignals(False)
        self.slider.blockSignals(False)
        self.length_label.setText(self.appearance.tr('words' if phrase else 'length'))
        self.symbols.setVisible(not phrase)
        self.explanation.setText(self.appearance.tr('phrase_hint' if phrase else 'password_hint'))
        self.regenerate()

    def regenerate(self, *_args):
        if self.mode.currentData() == 'phrase':
            value = generate_passphrase(self.length.value())
        else:
            value = generate_password(self.length.value(), self.symbols.isChecked())
        self.output.setPlainText(value)
        self.status.setText(self.appearance.tr('generator_privacy'))

    def value(self):
        return self.output.toPlainText()

    def copy_value(self):
        clipboard_guard().copy(self.value())
        self.status.setText(self.appearance.tr('copied'))
