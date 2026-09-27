import os
import sys
from pathlib import Path


def data_directory():
    if os.environ.get('VAULT_DATA_DIR'):
        return Path(os.environ['VAULT_DATA_DIR'])
    if sys.platform == 'darwin': return Path.home() / 'Library/Application Support/Appkaui/Vault'
    if sys.platform == 'win32': return Path(os.environ['LOCALAPPDATA']) / 'Appkaui/Vault'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share')) / 'Appkaui/Vault'
