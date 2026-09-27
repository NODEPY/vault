from dataclasses import replace

from core.models import PasswordEntry
from core.security import SessionCipher
from core.origins import canonical_origin


class VaultLockedError(Exception):
    pass
from storage.repository import VaultRepository


class Vault:
    def __init__(self, repository: VaultRepository, password: str, entries):
        self.repository = repository
        self._cipher = password if isinstance(password, SessionCipher) else SessionCipher(password)
        self._entries = {entry.id: replace(entry) for entry in entries}

    def save(self, entry: PasswordEntry):
        self.require_unlocked()
        if not entry.title.strip() or not entry.password:
            raise ValueError("Title and password are required")
        if entry.url:
            entry = replace(entry, url=canonical_origin(entry.url))
        updated = dict(self._entries)
        updated[entry.id] = replace(entry)
        # Оновлюємо пам'ять лише після успішного запису на диск.
        self.repository.save(list(updated.values()), self._cipher)
        self._entries = updated

    def get(self, entry_id: str) -> PasswordEntry:
        self.require_unlocked()
        return replace(self._entries[entry_id])

    def search(self, query: str = "") -> list[PasswordEntry]:
        self.require_unlocked()
        query = query.strip().casefold()
        results = [
            replace(entry)
            for entry in self._entries.values()
            if query in entry.title.casefold()
            or query in entry.username.casefold()
            or query in entry.url.casefold()
        ]
        return sorted(results, key=lambda entry: entry.title.casefold())


    @property
    def locked(self):
        return self._cipher is None

    def require_unlocked(self):
        if self.locked:
            raise VaultLockedError("Vault is locked")

    def lock(self):
        self._entries.clear()
        self._cipher = None

    def delete(self, entry_id):
        self.require_unlocked()
        updated = dict(self._entries)
        del updated[entry_id]
        self.repository.save(list(updated.values()), self._cipher)
        self._entries = updated

    def for_origin(self, origin):
        origin = canonical_origin(origin)
        return [entry for entry in self.search() if entry.url == origin]

    def import_entries(self, entries):
        from uuid import uuid4
        self.require_unlocked()
        updated = dict(self._entries)
        signatures = {(e.title, e.username, e.password, e.url, e.app_package, e.app_signature) for e in updated.values()}
        added = 0
        for entry in entries:
            signature = (entry.title, entry.username, entry.password, entry.url, entry.app_package, entry.app_signature)
            if signature in signatures: continue
            clone = replace(entry, id=uuid4().hex)
            updated[clone.id] = clone
            signatures.add(signature)
            added += 1
        self.repository.save(list(updated.values()), self._cipher)
        self._entries = updated
        return added
