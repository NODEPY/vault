"""Build a relocatable desktop folder and the Chrome native-messaging host."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
output=root/'dist'
cache=root/'build'
base=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--distpath',str(output),'--workpath',str(cache),'--specpath',str(cache)]
icon=root/'assets'/('vault.icns' if sys.platform=='darwin' else 'vault.ico')
args=['--additional-hooks-dir',str(root/'scripts/hooks'),'--name','Vault','--windowed','--onedir','--add-data',str(root/'ui/locales')+os.pathsep+'ui/locales','--add-data',str(root/'ui/assets')+os.pathsep+'ui/assets','--add-data',str(root/'ui/theme.qss')+os.pathsep+'ui','--add-data',str(root/'assets/vault-128.png')+os.pathsep+'assets']
if icon.exists():args+=['--icon',str(icon)]
if sys.platform=='darwin':args+=['--osx-bundle-identifier','com.appkaui.vault']
subprocess.run(base+args+[str(root/'main.py')],cwd=root,check=True)
subprocess.run(base+['--name','vault-bridge','--onedir','--console',str(root/'native_host_entry.py')],cwd=root,check=True)
if sys.platform=='darwin':
    destination=output/'native-host'
else:
    destination=output/'Vault/native-host'
if destination.exists():shutil.rmtree(destination)
shutil.move(str(output/'vault-bridge'),destination)
print('Built desktop app and native host in',output)
