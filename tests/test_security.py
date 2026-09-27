import unittest

from core.security import (
    VaultUnlockError,
    decrypt_data,
    encrypt_data,
)


class SecurityTests(unittest.TestCase):
    def test_round_trip(self):
        """Після розшифрування отримуємо початкові дані."""
        original = "Вигаданий запис для перевірки".encode("utf-8")
        encrypted = encrypt_data(original, "test-master-password")

        self.assertNotIn(original, encrypted)
        self.assertEqual(
            decrypt_data(encrypted, "test-master-password"),
            original,
        )

    def test_wrong_password(self):
        """Інший пароль не відкриває дані."""
        encrypted = encrypt_data(b"demo", "correct-password")

        with self.assertRaises(VaultUnlockError):
            decrypt_data(encrypted, "wrong-password")

    def test_tampered_data(self):
        """Змінені зашифровані дані не приймаються."""
        encrypted = bytearray(
            encrypt_data(b"demo", "test-master-password")
        )

        # Змінюємо байт усередині зашифрованої частини.
        encrypted[-10] ^= 1

        with self.assertRaises(VaultUnlockError):
            decrypt_data(bytes(encrypted), "test-master-password")

    def test_randomized_encryption(self):
        """Однакові дані щоразу шифруються по-різному."""
        first = encrypt_data(b"demo", "test-master-password")
        second = encrypt_data(b"demo", "test-master-password")

        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()