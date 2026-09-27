"""Archive bundles without losing executable bits or framework symlinks."""
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from core.version import VERSION
output=root/'dist';platform_name={'darwin':'macOS','win32':'Windows'}.get(sys.platform,'Linux')
name=f'Vault-{VERSION}-{platform_name}-{platform.machine()}'
notices=('LICENSE','README.md','docs','THIRD_PARTY_NOTICES.md','licenses')
if sys.platform=='win32':
    for item in notices:
        source=root/item;dest=output/'Vault'/item
        if source.is_dir():shutil.copytree(source,dest,dirs_exist_ok=True)
        else:shutil.copy2(source,dest)
    shutil.make_archive(str(output/name),'zip',output,'Vault')
elif sys.platform=='darwin':
    # File-provider managed directories may repeatedly add FinderInfo to .app
    # bundles. Seal the archive in a temporary directory outside that provider.
    with tempfile.TemporaryDirectory(prefix='vault-package-') as temporary:
        folder=Path(temporary)/'Vault';folder.mkdir()
        bundle=folder/'Vault.app'
        shutil.copytree(output/'Vault.app',bundle,symlinks=True)
        shutil.copytree(output/'native-host',folder/'native-host',symlinks=True)
        for attribute in ('com.apple.FinderInfo','com.apple.ResourceFork'):
            subprocess.run(['xattr','-dr',attribute,str(bundle)],check=True)
        subprocess.run(['codesign','--force','--deep','--sign','-','--timestamp=none',str(bundle)],check=True)
        subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True)
        with tarfile.open(output/(name+'.tar.gz'),'w:gz') as archive:
            archive.add(folder,arcname='Vault')
            for item in notices:archive.add(root/item,arcname='Vault/'+item)
else:
    with tarfile.open(output/(name+'.tar.gz'),'w:gz') as archive:
        archive.add(output/'Vault',arcname='Vault/Vault')
        for item in notices:archive.add(root/item,arcname='Vault/'+item)
print('Release archive:',name)
