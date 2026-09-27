# Модель запису: сервіс, логін, пароль, URL та нотатка.
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class PasswordEntry:
    title: str
    username: str
    password: str = field(repr=False)
    id: str = field(default_factory=lambda: uuid4().hex)
    url: str = ""
    app_package: str = ""
    app_signature: str = ""
