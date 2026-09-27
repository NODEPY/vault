import math
import string
import tempfile
import unittest
from pathlib import Path
from string import Formatter
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QDialog, QLineEdit
from PySide6.QtTest import QTest

from core.generator import WORDS, generate_password, generate_passphrase
from core.models import PasswordEntry
from core.settings import Preferences
from core.vault import Vault
from storage.repository import VaultRepository
from storage.settings_repository import SettingsRepository
from ui.appearance import Appearance
from ui.clipboard import clipboard_guard
from ui.entry_dialog import EntryDialog
from ui.generator_dialog import GeneratorDialog
from ui.i18n import load_language
from ui.main_window import MainWindow
from ui.themes import LANGUAGES, THEMES


class DesignFeaturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion')

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.appearance = Appearance()
        self.appearance.apply(Preferences())
        self.repo = VaultRepository(self.root/'vault.bin')
        self.record = PasswordEntry('Demo', 'fake-user', 'fake-password')
        self.vault = Vault(self.repo, 'fake-master-password', [self.record])
        self.addCleanup(clipboard_guard().clear_owned)

    def test_all_translations_have_matching_fields(self):
        english = load_language('en')
        fields = lambda text: {name for _, name, _, _ in Formatter().parse(text) if name is not None}
        for code, _ in LANGUAGES:
            language = load_language(code)
            self.assertEqual(set(language), set(english), code)
            for key, text in language.items():
                self.assertTrue(text.strip(), (code, key))
                self.assertEqual(fields(text), fields(english[key]), (code, key))

    def test_all_preferences_persist(self):
        repository = SettingsRepository(self.root/'settings.json')
        for language, _ in LANGUAGES:
            for theme in THEMES:
                preferences = Preferences(language, theme)
                repository.save(preferences)
                self.assertEqual(repository.load(), preferences)
                self.appearance.apply(preferences)
                self.assertNotIn('@BG@', self.app.styleSheet())
                self.assertNotIn('CHEVRON_PATH', self.app.styleSheet())

    def test_navigation_fits_every_language(self):
        window = MainWindow(self.vault, self.appearance)
        for language, _ in LANGUAGES:
            self.appearance.apply(Preferences(language, 'dark'))
            window.retranslate()
            for button in (window.all_button, window.generator_button, window.settings_button):
                self.assertGreaterEqual(window.sidebar.width() - 32, button.sizeHint().width())
        window.close()

    def test_password_options_and_bounds(self):
        for length in (12, 20, 64):
            for symbols in (False, True):
                result = generate_password(length, symbols)
                self.assertEqual(len(result), length)
                self.assertTrue(any(c.islower() for c in result))
                self.assertTrue(any(c.isupper() for c in result))
                self.assertTrue(any(c.isdigit() for c in result))
                self.assertEqual(any(c in '!@#$%&*+-=?' for c in result), symbols)
        for length in (0, 11, 65):
            with self.assertRaises(ValueError): generate_password(length)

    def test_passphrase_pool_and_selection(self):
        self.assertEqual(len(WORDS), len(set(WORDS)))
        self.assertGreaterEqual(8 * math.log2(len(WORDS)), 64)
        with patch('core.generator.secrets.choice', return_value=WORDS[0]) as choice:
            result = generate_passphrase()
        self.assertEqual(result.split('-'), [WORDS[0]] * 8)
        self.assertEqual(choice.call_count, 8)
        for count in (6, 8, 10):
            phrase = generate_passphrase(count).split('-')
            self.assertEqual(len(phrase), count)
            self.assertTrue(all(word in WORDS for word in phrase))
        with self.assertRaises(ValueError): generate_passphrase(5)

    def test_generator_modes(self):
        dialog = GeneratorDialog(self.appearance, allow_use=True)
        self.assertEqual(len(dialog.value()), 20)
        dialog.mode.setCurrentIndex(1)
        self.assertEqual(len(dialog.value().split('-')), 8)
        dialog.length.setValue(10)
        self.assertEqual(len(dialog.value().split('-')), 10)
        dialog.mode.setCurrentIndex(0)
        self.assertEqual(len(dialog.value()), 20)
        dialog.reject()

    def test_generator_cancel_preserves_entry_password(self):
        dialog = EntryDialog(entry=self.record, appearance=self.appearance)
        with patch.object(GeneratorDialog, 'exec', return_value=QDialog.DialogCode.Rejected):
            dialog.open_generator()
        self.assertEqual(dialog.password_input.text(), self.record.password)
        with patch.object(GeneratorDialog, 'exec', return_value=QDialog.DialogCode.Accepted), patch.object(GeneratorDialog, 'value', return_value='generated-test-value'):
            dialog.open_generator()
        self.assertEqual(dialog.password_input.text(), 'generated-test-value')
        self.assertEqual(self.record.password, 'fake-password')

    def test_clipboard_owns_only_its_copy(self):
        guard = clipboard_guard()
        guard.copy('fake-secret')
        self.assertEqual(self.app.clipboard().text(), 'fake-secret')
        self.assertEqual(guard.timer.interval(), 20000)
        guard.clear_owned()
        self.assertEqual(self.app.clipboard().text(), '')
        guard.copy('another-fake-secret')
        self.app.clipboard().setText('user copied something else')
        guard.clear_owned()
        self.assertEqual(self.app.clipboard().text(), 'user copied something else')
        self.app.clipboard().clear()

    def test_detail_selection_and_reveal_timeout(self):
        window = MainWindow(self.vault, self.appearance)
        self.assertEqual(window.username_value.text(), self.record.username)
        self.assertEqual(window.password_value.echoMode(), QLineEdit.EchoMode.Password)
        window.toggle_password()
        self.assertEqual(window.hide_timer.interval(), 10000)
        self.assertEqual(window.password_value.echoMode(), QLineEdit.EchoMode.Normal)
        window.hide_timer.start(1)
        QTest.qWait(20)
        self.assertEqual(window.password_value.echoMode(), QLineEdit.EchoMode.Password)
        window.search.setText('absent')
        self.assertEqual(window.password_value.text(), '')
        self.assertIsNone(window.selected_id)
        self.assertFalse(window.edit_button.isEnabled())
        window.close()

    def test_new_entry_selection_matches_saved_id(self):
        window = MainWindow(self.vault, self.appearance)
        dialog = EntryDialog(appearance=self.appearance)
        dialog.title_input.setText('A new test')
        dialog.password_input.setText('fake-password')
        with patch.object(dialog, 'exec', return_value=QDialog.DialogCode.Accepted):
            self.assertTrue(window.save_dialog(dialog))
        selected_id = window.selected_id
        window.refresh_entries()
        self.assertEqual(window.selected_id, selected_id)
        self.assertEqual(window.detail_title.text(), 'A new test')
        self.assertEqual(len(self.repo.load('fake-master-password')), 2)
        window.close()


if __name__ == '__main__':
    unittest.main()
