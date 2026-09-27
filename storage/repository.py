import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from core.models import PasswordEntry
from core.security import SessionCipher, decrypt_data, encrypt_data
from core.origins import canonical_origin


class VaultFormatError(Exception):
    """Дані сховища мають неправильну структуру."""


class VaultRepository:
    def __init__(self, path: Path):
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.is_file()

    def load(self, password: str) -> list[PasswordEntry]:
        """Читаємо, розшифровуємо та перевіряємо записи."""
        if self.path.stat().st_size > 16 * 1024 * 1024:
            raise VaultFormatError("Vault exceeds the 16 MiB size limit.")
        encrypted = self.path.read_bytes()
        decrypted = decrypt_data(encrypted, password)

        try:
            data = json.loads(decrypted.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise VaultFormatError(
                "Не вдалося прочитати структуру сховища."
            ) from None

        if not isinstance(data, list):
            raise VaultFormatError("Очікувався список записів.")

        entries = []
        seen_ids = set()
        required_fields = {"id", "title", "username", "password"}

        for item in data:
            if not isinstance(item, dict):
                raise VaultFormatError("Некоректний запис.")

            if not required_fields.issubset(item) or set(item) - (required_fields | {"url", "app_package", "app_signature"}):
                raise VaultFormatError("Некоректні поля запису.")

            if not all(isinstance(value, str) for value in item.values()):
                raise VaultFormatError(
                    "Поля запису повинні містити текст."
                )

            if not item["id"] or not item["title"].strip():
                raise VaultFormatError(
                    "Запис не має ідентифікатора або назви."
                )

            if item["id"] in seen_ids:
                raise VaultFormatError(
                    "Знайдено повторний ідентифікатор."
                )

            if item.get("url"):
                try:
                    item["url"] = canonical_origin(item["url"])
                except (ValueError, UnicodeError):
                    raise VaultFormatError("Invalid website address") from None
            seen_ids.add(item["id"])
            entries.append(PasswordEntry(**item))

        return entries

    def save(self, entries: list[PasswordEntry], password: str):
        """Шифруємо записи та замінюємо файл сховища."""
        data = [asdict(entry) for entry in entries]

        plaintext = json.dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")

        # На диск потрапляють тільки зашифровані дані.
        encrypted = password.encrypt(plaintext) if isinstance(password, SessionCipher) else encrypt_data(plaintext, password)
        if len(encrypted) > 16 * 1024 * 1024:
            raise ValueError("Vault exceeds the 16 MiB size limit.")

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
            mode=0o700,
        )

        # Тимчасовий файл створюємо в тій самій папці.
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
        )

        temporary_path = Path(temporary_name)

        try:
            with os.fdopen(descriptor, "wb") as file:
                file.write(encrypted)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.path)
        finally:
            # При помилці прибираємо тимчасовий файл.
            temporary_path.unlink(missing_ok=True)

    def delete_all(self):
        """Видаляє локальне сховище. Викликати лише після підтвердження в UI."""
        self.path.unlink()
