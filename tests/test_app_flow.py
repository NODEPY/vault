import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QDialog

from core.models import PasswordEntry
from core.vault import Vault
from storage.repository import VaultRepository
from ui.main_window import MainWindow
from ui.unlock_window import UnlockDialog


class AppFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.repo = VaultRepository(Path(folder.name) / "vault.bin")
        self.password = "only-a-test-master-password"

    def create_vault(self):
        dialog = UnlockDialog(self.repo)
        dialog.password_input.setText(self.password)
        dialog.confirm_input.setText(self.password)
        dialog.unlock()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        return dialog.vault

    def test_create_save_reopen_and_edit(self):
        vault = self.create_vault()
        entry = PasswordEntry("Demo", "demo@example.com", "fake-password")
        vault.save(entry)
        login = UnlockDialog(self.repo)
        self.assertFalse(login.creating)
        login.password_input.setText(self.password)
        login.unlock()
        self.assertEqual(login.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(login.vault.search("EXAMPLE"), [entry])
        entry.title = "Updated"
        login.vault.save(entry)
        self.assertEqual(self.repo.load(self.password)[0].title, "Updated")
        self.assertEqual(login.password_input.text(), "")

    def test_wrong_password_preserves_vault(self):
        self.create_vault()
        before = self.repo.path.read_bytes()
        login = UnlockDialog(self.repo)
        login.password_input.setText("wrong-password")
        login.unlock()
        self.assertIsNone(login.vault)
        self.assertTrue(login.error_label.text())
        self.assertEqual(self.repo.path.read_bytes(), before)

    def test_create_validation_and_cancel(self):
        dialog = UnlockDialog(self.repo)
        dialog.password_input.setText("short")
        dialog.confirm_input.setText("short")
        dialog.unlock()
        self.assertFalse(self.repo.exists())
        dialog.password_input.setText(self.password)
        dialog.confirm_input.setText("different")
        dialog.unlock()
        self.assertFalse(self.repo.exists())
        dialog.reject()
        self.assertIsNone(dialog.vault)

    def test_failed_save_does_not_change_memory(self):
        vault = self.create_vault()
        entry = PasswordEntry("Original", "demo", "fake-password")
        vault.save(entry)
        edited = vault.get(entry.id)
        edited.title = "Changed"
        with patch.object(self.repo, "save", side_effect=OSError("test")):
            with self.assertRaises(OSError):
                vault.save(edited)
        self.assertEqual(vault.get(entry.id).title, "Original")
        self.assertEqual(self.repo.load(self.password)[0].title, "Original")

    def test_corrupt_file_is_not_replaced(self):
        self.repo.path.write_bytes(b"corrupt-file")
        login = UnlockDialog(self.repo)
        self.assertFalse(login.creating)
        login.password_input.setText(self.password)
        login.unlock()
        self.assertIsNone(login.vault)
        self.assertEqual(self.repo.path.read_bytes(), b"corrupt-file")

    def test_window_filters_loaded_records(self):
        vault = self.create_vault()
        vault.save(PasswordEntry("Demo", "demo-user", "fake-password"))
        window = MainWindow(vault)
        self.assertEqual(window.entries.count(), 1)
        window.search.setText("absent")
        self.assertEqual(window.entries.count(), 0)
        window.search.setText("DEMO-USER")
        self.assertEqual(window.entries.count(), 1)
        window.close()

    def test_second_lock_is_denied(self):
        path = str(self.repo.path.parent / "vault.lock")
        first, second = QLockFile(path), QLockFile(path)
        first.setStaleLockTime(0)
        second.setStaleLockTime(0)
        self.assertTrue(first.tryLock(0))
        self.addCleanup(first.unlock)
        self.assertFalse(second.tryLock(0))


if __name__ == "__main__":
    unittest.main()
