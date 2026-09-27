"""Verify the JVM test's Fernet output with the desktop implementation."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from core.security import decrypt_data
path=root/'android/app/build/interop-java.vault'
plain=decrypt_data(path.read_bytes(),'interop-only-пароль-🔐')
expected='[{"id":"interop","title":"Тест","username":"demo","password":"fake-🔑"}]'.encode()
assert plain==expected
print('PASS: Android Java encryption decrypts identically in Python.')
