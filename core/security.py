import base64
import secrets

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


# Позначка формату нашого зашифрованого файлу.
HEADER = b"VAULT1\x00"

# Сіль — випадкові дані для отримання ключа.
# Вона не є секретом і зберігається поруч із шифротекстом.
SALT_SIZE = 16


class VaultUnlockError(Exception):
    """Неправильний пароль або пошкоджене сховище."""


def _make_cipher(password: str, salt: bytes) -> Fernet:
    """Отримуємо ключ шифрування з майстер-пароля."""
    kdf = Argon2id(
        salt=salt,
        length=32,
        iterations=3,
        lanes=4,
        memory_cost=64 * 1024,
    )

    key = kdf.derive(password.encode("utf-8"))

    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_data(data: bytes, password: str) -> bytes:
    """Шифруємо дані. Повертаємо вміст майбутнього файлу."""
    if not password:
        raise ValueError("Майстер-пароль не може бути порожнім.")

    salt = secrets.token_bytes(SALT_SIZE)
    cipher = _make_cipher(password, salt)

    encrypted = cipher.encrypt(data)

    return HEADER + salt + encrypted


def decrypt_data(content: bytes, password: str) -> bytes:
    """Розшифровуємо дані та перевіряємо їхню цілісність."""
    if not content.startswith(HEADER):
        raise VaultUnlockError(
            "Невідомий формат або пошкоджене сховище."
        )

    salt_start = len(HEADER)
    salt_end = salt_start + SALT_SIZE

    if len(content) <= salt_end:
        raise VaultUnlockError("Файл сховища пошкоджено.")

    salt = content[salt_start:salt_end]
    encrypted = content[salt_end:]

    cipher = _make_cipher(password, salt)

    try:
        return cipher.decrypt(encrypted)
    except InvalidToken:
        raise VaultUnlockError(
            "Неправильний майстер-пароль або пошкоджене сховище."
        ) from None

class SessionCipher:
    """Keeps only the derived encryption key during an unlocked session."""
    def __init__(self, password: str, salt=None):
        if not password:
            raise ValueError("Empty master password")
        self.salt = salt if salt is not None else secrets.token_bytes(SALT_SIZE)
        self.cipher = _make_cipher(password, self.salt)

    def encrypt(self, data: bytes) -> bytes:
        return HEADER + self.salt + self.cipher.encrypt(data)
