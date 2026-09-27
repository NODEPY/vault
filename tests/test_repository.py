import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.models import PasswordEntry
from core.security import VaultUnlockError
from storage.repository import VaultRepository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

        self.path = Path(self.directory.name) / "vault.bin"
        self.repository = VaultRepository(self.path)

        self.password = "test-master-password"
        self.entry = PasswordEntry(
            title="Тестовий сервіс",
            username="demo@example.com",
            password="fake-entry-password",
        )

    def test_save_and_load(self):
        """Записи зберігаються та читаються без змін."""
        self.repository.save([self.entry], self.password)

        # Новий об'єкт імітує повторне відкриття сховища.
        reopened = VaultRepository(self.path)
        loaded = reopened.load(self.password)

        self.assertTrue(reopened.exists())
        self.assertEqual(loaded, [self.entry])

    def test_file_is_encrypted(self):
        """Логін і пароль не записуються відкритим текстом."""
        self.repository.save([self.entry], self.password)
        content = self.path.read_bytes()

        self.assertNotIn(self.entry.username.encode(), content)
        self.assertNotIn(self.entry.password.encode(), content)
        self.assertNotIn(self.password.encode(), content)

    def test_wrong_password_preserves_file(self):
        """Невдала спроба входу не змінює файл."""
        self.repository.save([self.entry], self.password)
        before = self.path.read_bytes()

        with self.assertRaises(VaultUnlockError):
            self.repository.load("wrong-password")

        self.assertEqual(self.path.read_bytes(), before)

    def test_failed_save_preserves_previous_data(self):
        """Помилка заміни файла залишає попередні записи."""
        self.repository.save([self.entry], self.password)
        before = self.path.read_bytes()

        with patch(
            "storage.repository.os.replace",
            side_effect=OSError("Тестова помилка запису"),
        ):
            with self.assertRaises(OSError):
                self.repository.save([], self.password)

        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(
            self.repository.load(self.password),
            [self.entry],
        )

        # Тимчасові файли після помилки прибрані.
        self.assertEqual(
            set(self.path.parent.iterdir()),
            {self.path},
        )

    def test_missing_file_is_not_created_on_load(self):
        """Читання відсутнього файла не створює сховище."""
        with self.assertRaises(FileNotFoundError):
            self.repository.load(self.password)

        self.assertFalse(self.repository.exists())


if __name__ == "__main__":
    unittest.main()