"""Render promotional previews using only fictitious entries and a temporary vault."""
import sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from PySide6.QtWidgets import QApplication
from core.settings import Preferences
from core.models import PasswordEntry
from core.vault import Vault
from storage.repository import VaultRepository
from ui.main_window import MainWindow
from ui.appearance import Appearance
app=QApplication([]);app.setStyle('Fusion')
output=Path(sys.argv[1] if len(sys.argv)>1 else root/'dist/previews');output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
    vault=Vault(VaultRepository(Path(folder)/'vault.bin'),'preview-only-master-password',[])
    for title,user,site in [('GitHub','alex@example.com','https://github.com'),('Figma','alex.studio@example.com','https://figma.com'),('Linear','alex@example.com','https://linear.app'),('Proton','alex.demo@proton.me','https://account.proton.me'),('Spotify','alex.demo','https://accounts.spotify.com')]:vault.save(PasswordEntry(title,user,'fictional-preview-password',url=site))
    appearance=Appearance()
    for theme in ('dark','light','sand','forest','midnight'):
        appearance.apply(Preferences(theme=theme));window=MainWindow(vault,appearance);window.resize(1120,740);window.show();app.processEvents();window.grab().save(str(output/f'vault-{theme}.png'));window.close()
