from pathlib import Path
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from core.settings import Preferences
from ui.i18n import translate
from ui.themes import THEMES


class Appearance:
    def __init__(self, preferences=None, repository=None):
        self.preferences = preferences or Preferences()
        self.repository = repository

    @property
    def colors(self):
        return THEMES[self.preferences.theme]

    def tr(self, key, **values):
        return translate(key, self.preferences.language, **values)

    def apply(self, preferences):
        colors = THEMES[preferences.theme]
        stylesheet = Path(__file__).with_name('theme.qss').read_text(encoding='utf-8')
        for key, color in colors.items():
            stylesheet = stylesheet.replace('@' + key.upper() + '@', color)
        arrow = Path(__file__).parent / 'assets' / f"chevron-{colors['mode']}.svg"
        stylesheet = stylesheet.replace('CHEVRON_PATH', arrow.as_posix())
        app = QApplication.instance()
        # Native controls and placeholder text must match the selected theme too.
        palette = QPalette()
        roles = {
            QPalette.ColorRole.Window: 'bg', QPalette.ColorRole.WindowText: 'fg',
            QPalette.ColorRole.Base: 'field', QPalette.ColorRole.AlternateBase: 'panel',
            QPalette.ColorRole.Text: 'fg', QPalette.ColorRole.Button: 'panel',
            QPalette.ColorRole.ButtonText: 'fg', QPalette.ColorRole.Highlight: 'selected',
            QPalette.ColorRole.HighlightedText: 'fg', QPalette.ColorRole.PlaceholderText: 'muted',
            QPalette.ColorRole.ToolTipBase: 'panel', QPalette.ColorRole.ToolTipText: 'fg',
        }
        for role, key in roles.items(): palette.setColor(role, QColor(colors[key]))
        app.setPalette(palette)
        app.setStyleSheet(stylesheet)
        self.preferences = preferences

    def save(self, preferences):
        if self.repository is not None: self.repository.save(preferences)
        self.apply(preferences)
