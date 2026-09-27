import json
import os
import re
import shlex
import sys
from pathlib import Path

from browser_bridge.config import EXTENSION_ID, HOST_NAME
from browser_bridge.paths import data_directory


def register_chrome(extension_id=EXTENSION_ID, directory=None, manifest_directory=None):
    if not re.fullmatch('[a-p]{32}', extension_id):
        raise ValueError('A Chrome extension ID contains exactly 32 letters from a to p.')
    install_windows_registry = os.name == 'nt' and manifest_directory is None
    directory = Path(directory or data_directory())
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    if getattr(sys,'frozen',False):
        # Packaged host is distributed alongside the desktop app.
        app_parent = Path(sys.executable).resolve()
        if sys.platform == 'darwin':
            host = app_parent.parents[2].parent/'native-host'/'vault-bridge'
        else:
            host = app_parent.parent/'native-host'/('vault-bridge.exe' if os.name=='nt' else 'vault-bridge')
    else:
        script = Path(__file__).resolve().parents[1]/'native_host_entry.py'
        if os.name == 'nt':
            host = directory/'vault-bridge.cmd'
            host.write_text('@echo off\r\n"'+sys.executable+'" "'+str(script)+'" %*\r\n')
        else:
            host = directory/'vault-bridge'
            host.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(script))+' "$@"\n')
            host.chmod(0o700)
    if not host.is_file(): raise FileNotFoundError('Native host is missing. Keep the native-host folder beside Vault.')
    if manifest_directory is None:
        if sys.platform == 'darwin': manifest_directory=Path.home()/'Library/Application Support/Google/Chrome/NativeMessagingHosts'
        elif sys.platform == 'win32': manifest_directory=directory/'native-manifests'
        else: manifest_directory=Path.home()/'.config/google-chrome/NativeMessagingHosts'
    manifest_directory=Path(manifest_directory)
    manifest_directory.mkdir(parents=True,exist_ok=True)
    path=manifest_directory/(HOST_NAME+'.json')
    path.write_text(json.dumps({'name':HOST_NAME,'description':'Vault local password manager','path':str(host),'type':'stdio','allowed_origins':['chrome-extension://'+extension_id+'/']},indent=2))
    if install_windows_registry:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 'Software\\Google\\Chrome\\NativeMessagingHosts\\'+HOST_NAME) as key:
            winreg.SetValueEx(key,'',0,winreg.REG_SZ,str(path))
    (directory/'chrome-registration.json').write_text(json.dumps({'extension_ids':[extension_id]}))
    return path
