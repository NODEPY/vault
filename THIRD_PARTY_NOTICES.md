# Third-party notices

Vault uses unmodified third-party libraries. Their original licenses and attribution documents are in `licenses/` and remain applicable independently of Vault's own licensing.

- Python 3.14: PSF license and included notices; https://www.python.org/downloads/source/
- Qt / PySide6 / Shiboken6 6.11.2: LGPLv3 with applicable GPLv3 terms and third-party component notices. Qt is dynamically linked and can be replaced/rebuilt with compatible modified versions. Source: https://code.qt.io/cgit/qt/qtbase.git/?h=v6.11.2 and https://code.qt.io/cgit/pyside/pyside-setup.git/?h=v6.11.2; additional SVG source https://code.qt.io/cgit/qt/qtsvg.git/?h=v6.11.2. See https://doc.qt.io/qt-6/licensing.html and https://doc.qt.io/qt-6/licenses-used-in-qt.html. No restriction on reverse engineering for debugging modifications to these libraries is imposed by this package.
- cryptography 50.0.1: Apache 2.0 / BSD; its binary distribution includes OpenSSL. https://github.com/pyca/cryptography/tree/50.0.1
- CFFI 2.1.1 and pycparser 3.0: their included license texts; https://github.com/python-cffi/cffi and https://github.com/eliben/pycparser
- PyInstaller 6.22.3: GPL with the bootloader/distribution exception; https://github.com/pyinstaller/pyinstaller/tree/v6.22.3
- Bouncy Castle bcprov-jdk18on 1.86: included Bouncy Castle license, also embedded in the Android app's assets. https://www.bouncycastle.org/download/bouncy-castle-java/

Qt attribution pages in `licenses/Qt/` were retrieved from official Qt documentation for Qt 6.11.2. Build/test tooling is not shipped as part of the installed applications. Dependency source and license availability must be retained by the publisher with any redistributed binary release.
