import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QDialog

from core.models import PasswordEntry
from core.security import VaultUnlockError
from core.settings import Preferences
from storage.repository import VaultRepository
from storage.settings_repository import SettingsFormatError, SettingsRepository
from ui.appearance import Appearance
from ui.entry_dialog import EntryDialog
from ui.main_window import MainWindow
from ui.reset_dialog import ResetDialog
from ui.settings_dialog import SettingsDialog
from ui.unlock_window import UnlockDialog


class SettingsResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.settings = SettingsRepository(self.root / 'settings.json')
        self.appearance = Appearance(repository=self.settings)
        self.appearance.apply(self.appearance.preferences)
        self.repo = VaultRepository(self.root / 'vault.bin')
        self.password = 'temporary-master-password'

    def existing_vault(self):
        self.repo.save([PasswordEntry('Test', 'fake-user', 'fake-pass')], self.password)
        return UnlockDialog(self.repo, self.appearance)

    def test_first_run_defaults_and_cancel(self):
        dialog = SettingsDialog(self.appearance, onboarding=True)
        self.assertEqual(dialog.title.text(), 'Welcome to Vault')
        dialog.language_combo.setCurrentIndex(0)
        dialog.theme_combo.setCurrentIndex(1)
        self.assertEqual(self.appearance.preferences, Preferences('uk', 'light'))
        dialog.reject()
        self.assertEqual(self.appearance.preferences, Preferences('en', 'dark'))
        self.assertFalse(self.settings.path.exists())
        self.assertFalse(self.repo.exists())

    def test_settings_persist_without_touching_vault(self):
        self.existing_vault()
        before = self.repo.path.read_bytes()
        dialog = SettingsDialog(self.appearance, onboarding=True)
        dialog.language_combo.setCurrentIndex(0)
        dialog.theme_combo.setCurrentIndex(1)
        dialog.save_settings()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(self.settings.load(), Preferences('uk', 'light'))
        self.assertEqual(self.repo.path.read_bytes(), before)
        loaded = Appearance(self.settings.load(), self.settings)
        login = UnlockDialog(self.repo, loaded)
        self.assertEqual(login.title.text(), 'Відкрий сховище')

    def test_failed_settings_write_and_cancel(self):
        self.settings.save(Preferences())
        before = self.settings.path.read_bytes()
        dialog = SettingsDialog(self.appearance)
        dialog.language_combo.setCurrentIndex(0)
        dialog.theme_combo.setCurrentIndex(1)
        with patch('storage.settings_repository.os.replace', side_effect=OSError('test')):
            dialog.save_settings()
        self.assertTrue(dialog.error_label.text())
        self.assertNotEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(self.settings.path.read_bytes(), before)
        dialog.reject()
        self.assertEqual(self.appearance.preferences, Preferences())
        self.assertEqual(set(self.root.iterdir()), {self.settings.path})

    def test_invalid_settings_leave_vault_intact(self):
        self.existing_vault()
        before = self.repo.path.read_bytes()
        for content in (b'broken', b'\xff', b'{"language":"xx","theme":"dark"}'):
            self.settings.path.write_bytes(content)
            with self.assertRaises(SettingsFormatError):
                self.settings.load()
        self.assertEqual(self.repo.path.read_bytes(), before)

    def test_reset_requires_exact_confirmation(self):
        for language, token in [('en', 'DELETE'), ('uk', 'ВИДАЛИТИ')]:
            dialog = ResetDialog(Appearance(Preferences(language, 'dark')))
            self.assertFalse(dialog.delete_button.isEnabled())
            dialog.confirm_input.setText('wrong')
            dialog.confirm()
            self.assertFalse(dialog.delete_button.isEnabled())
            self.assertNotEqual(dialog.result(), QDialog.DialogCode.Accepted)
            dialog.confirm_input.setText(token)
            self.assertTrue(dialog.delete_button.isEnabled())
            dialog.confirm()
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)

    def test_cancel_reset_preserves_data(self):
        login = self.existing_vault()
        before = self.repo.path.read_bytes()
        with patch.object(ResetDialog, 'exec', return_value=QDialog.DialogCode.Rejected):
            login.reset_vault()
        self.assertEqual(self.repo.path.read_bytes(), before)
        self.assertNotEqual(login.result(), UnlockDialog.RESET_RESULT)

    def test_confirmed_reset_then_new_master_password(self):
        login = self.existing_vault()
        self.settings.save(Preferences('uk', 'light'))
        before = self.settings.path.read_bytes()
        def confirm(dialog):
            dialog.confirm_input.setText(dialog.token)
            dialog.confirm()
            return dialog.result()
        with patch.object(ResetDialog, 'exec', confirm):
            login.reset_vault()
        self.assertEqual(login.result(), UnlockDialog.RESET_RESULT)
        self.assertFalse(self.repo.exists())
        self.assertEqual(self.settings.path.read_bytes(), before)
        fresh = UnlockDialog(self.repo, self.appearance)
        self.assertTrue(fresh.creating)
        fresh.password_input.setText('different-master-password')
        fresh.confirm_input.setText('different-master-password')
        fresh.unlock()
        self.assertEqual(fresh.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(self.repo.load('different-master-password'), [])
        with self.assertRaises(VaultUnlockError):
            self.repo.load(self.password)

    def test_failed_delete_does_not_start_new_vault(self):
        login = self.existing_vault()
        before = self.repo.path.read_bytes()
        with patch.object(ResetDialog, 'exec', return_value=QDialog.DialogCode.Accepted), patch.object(self.repo, 'delete_all', side_effect=OSError('test')):
            login.reset_vault()
        self.assertEqual(self.repo.path.read_bytes(), before)
        self.assertNotEqual(login.result(), UnlockDialog.RESET_RESULT)
        self.assertTrue(login.error_label.text())

    def test_main_and_entry_language_changes(self):
        login = self.existing_vault()
        login.password_input.setText(self.password)
        login.unlock()
        main = MainWindow(login.vault, self.appearance)
        self.assertEqual(main.title.text(), 'Your passwords')
        self.appearance.save(Preferences('uk', 'light'))
        main.retranslate()
        self.assertEqual(main.title.text(), 'Твої паролі')
        self.assertEqual(main.entries.count(), 1)
        dialog = EntryDialog(main, appearance=self.appearance)
        self.assertEqual(dialog.windowTitle(), 'Новий запис')
        dialog.validate_and_accept()
        self.assertEqual(dialog.error_label.text(), 'Введи назву сервісу.')
        main.close()


if __name__ == '__main__':
    unittest.main()
