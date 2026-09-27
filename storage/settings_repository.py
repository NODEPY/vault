import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from core.settings import Preferences


class SettingsFormatError(Exception):
    pass


class SettingsRepository:
    """Зберігає тільки мову та тему. Паролів у цьому файлі немає."""

    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except UnicodeError as error:
            raise SettingsFormatError("Invalid settings encoding") from error
        try:
            data = json.loads(content)
            if not isinstance(data, dict) or (not {"language", "theme"}.issubset(data) or set(data) - {"language", "theme", "auto_lock_minutes"}):
                raise ValueError("Invalid settings fields")
            return Preferences(**data)
        except (UnicodeError, ValueError, TypeError) as error:
            raise SettingsFormatError("Invalid settings file") from error

    def save(self, preferences: Preferences):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, name = tempfile.mkstemp(dir=self.path.parent, prefix=".settings-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(asdict(preferences), file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(name, self.path)
        finally:
            Path(name).unlink(missing_ok=True)
