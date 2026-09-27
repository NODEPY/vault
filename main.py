import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from storage.repository import VaultRepository
from storage.settings_repository import SettingsFormatError, SettingsRepository
from ui.appearance import Appearance
from ui.session import SessionController
from ui.settings_dialog import SettingsDialog
from ui.unlock_window import UnlockDialog


def main():
    if sys.argv[1:] == ["--smoke-test"]:
        from scripts.smoke_test import run
        return run()
    if sys.argv[1:] == ["--version"]:
        from core.version import VERSION
        print(VERSION)
        return 0
    app = QApplication(sys.argv)
    app.setOrganizationName("Appkaui")
    app.setApplicationName("Vault")
    app.setStyle("Fusion")
    from PySide6.QtGui import QIcon
    app.setWindowIcon(QIcon(str(Path(__file__).parent/"assets/vault-128.png")))
    app.setQuitOnLastWindowClosed(False)
    appearance = Appearance()
    appearance.apply(appearance.preferences)
    import os
    location = os.environ.get("VAULT_DATA_DIR") or QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    if not location:
        QMessageBox.critical(None, appearance.tr("error"), appearance.tr("location_error"))
        return 1
    data_directory = Path(location)
    try:
        data_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    except OSError:
        QMessageBox.critical(None, appearance.tr("error"), appearance.tr("location_error"))
        return 1

    # Блокування охоплює і вхід, і скидання, і відкриту сесію.
    lock = QLockFile(str(data_directory / "vault.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.warning(None, appearance.tr("vault_busy"), appearance.tr("lock_error"))
        return 1

    try:
        settings_repository = SettingsRepository(data_directory / "settings.json")
        appearance.repository = settings_repository
        try:
            preferences = settings_repository.load()
        except SettingsFormatError:
            preferences = None
            QMessageBox.warning(None, appearance.tr("settings"), appearance.tr("settings_invalid"))
        except OSError:
            QMessageBox.critical(None, appearance.tr("error"), appearance.tr("file_error"))
            return 1

        if preferences is None:
            setup = SettingsDialog(appearance, onboarding=True)
            if setup.exec() != QDialog.DialogCode.Accepted:
                return 0
            setup.deleteLater()
        else:
            appearance.apply(preferences)

        repository = VaultRepository(data_directory / "vault.bin")
        controller = SessionController(repository, appearance, app)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, controller.unlock)
        try:
            return app.exec()
        finally:
            controller.shutdown()
    finally:
        lock.unlock()


if __name__ == "__main__":
    sys.exit(main())
