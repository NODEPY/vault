"""Explicit packaged-app check; uses only a temporary, fictitious vault."""
def run():
    import tempfile
    from pathlib import Path
    from PySide6.QtWidgets import QApplication
    from core.models import PasswordEntry
    from core.vault import Vault
    from storage.repository import VaultRepository
    from ui.appearance import Appearance
    from ui.main_window import MainWindow
    app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix='vault-smoke-') as folder:
        repository=VaultRepository(Path(folder)/'vault.bin')
        vault=Vault(repository,'smoke-test-only-master',[])
        vault.save(PasswordEntry('Demo','demo@example.com','fictional-test-password',url='https://example.com'))
        assert repository.load('smoke-test-only-master')[0].title=='Demo'
        appearance=Appearance();appearance.apply(appearance.preferences)
        window=MainWindow(vault,appearance);window.show();app.processEvents()
        assert window.entries.count()==1
        window.close();vault.lock()
    return 0
