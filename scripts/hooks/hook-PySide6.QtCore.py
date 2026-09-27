"""Collect the desktop Qt dependencies without unused PDF/virtual-keyboard plugins."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies
hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries = [(source, destination) for source, destination in binaries
            if not any(name in Path(source).name.lower() for name in ('qpdf', 'qtvirtualkeyboard'))]
