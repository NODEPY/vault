from dataclasses import dataclass


@dataclass(frozen=True)
class Preferences:
    language: str = "en"
    theme: str = "dark"
    auto_lock_minutes: int = 5

    def __post_init__(self):
        if self.language not in ("uk", "en", "pl", "de", "es"):
            raise ValueError("Unsupported language")
        if self.theme not in ("dark", "light", "sand", "forest", "midnight"):
            raise ValueError("Unsupported theme")

        if type(self.auto_lock_minutes) is not int or self.auto_lock_minutes not in (1, 5, 15, 30):
            raise ValueError("Invalid automatic lock interval")
