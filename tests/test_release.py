import io
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from PySide6.QtWidgets import QApplication, QMessageBox
from browser_bridge.config import EXTENSION_ID, MAX_MESSAGE
from browser_bridge.native_host import relay
from browser_bridge.protocol import read_message, write_message
from browser_bridge.register import register_chrome
from browser_bridge.server import BridgeServer
from core.models import PasswordEntry
from core.origins import canonical_origin
from core.security import encrypt_data
from core.vault import Vault, VaultLockedError
from storage.repository import VaultRepository
from ui.appearance import Appearance
from ui.session import SessionController


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.directory=Path(folder.name);self.repo=VaultRepository(self.directory/'vault.bin')
        self.master='test-only-master-password'
        self.vault=Vault(self.repo,self.master,[])
    def test_exact_origin(self):
        self.assertEqual(canonical_origin('https://EXAMPLE.com:443/login'), 'https://example.com')
        for value in ('http://example.com','https://user@example.com','javascript:alert(1)','https://example.com:99999','https://bad host.com',''):
            with self.subTest(value=value),self.assertRaises((ValueError,UnicodeError)):canonical_origin(value)
        self.vault.save(PasswordEntry('Demo','user','fake',url='https://example.com/login'))
        self.assertEqual(len(self.vault.for_origin('https://example.com')),1)
        for value in ('https://evil.example.com','https://example.com.evil.test','https://example.com:444'):
            self.assertEqual(self.vault.for_origin(value),[])
    def test_old_vault_migration_and_android_fields(self):
        self.repo.path.write_bytes(encrypt_data(json.dumps([{'id':'old','title':'Old','username':'u','password':'p'}]).encode(),self.master))
        old=self.repo.load(self.master)[0];self.assertEqual(old.url,'')
        old.app_package='com.example.demo';old.app_signature='f'*64
        self.vault.save(old);self.assertEqual(self.repo.load(self.master)[0].app_signature,'f'*64)
    def test_delete_failure_and_lock(self):
        entry=PasswordEntry('Demo','u','fake');self.vault.save(entry);before=self.repo.path.read_bytes()
        with patch.object(self.repo,'save',side_effect=OSError),self.assertRaises(OSError):self.vault.delete(entry.id)
        self.assertEqual(self.vault.get(entry.id),entry);self.assertEqual(self.repo.path.read_bytes(),before)
        self.vault.delete(entry.id);self.assertEqual(self.repo.load(self.master),[])
        self.vault.lock()
        with self.assertRaises(VaultLockedError):self.vault.search()
        with self.assertRaises(VaultLockedError):self.vault.save(entry)
        self.assertFalse(hasattr(self.vault,'_password'))
    def test_import_merge_preserves_entries_and_current_password(self):
        a=PasswordEntry('Existing','u','fake');b=PasswordEntry('Imported','new','fake2',id=a.id)
        self.vault.save(a);self.assertEqual(self.vault.import_entries([a,b,b]),1)
        loaded=self.repo.load(self.master);self.assertEqual(len(loaded),2);self.assertEqual(len({x.id for x in loaded}),2)
    def test_protocol_bounds_truncation_and_roundtrip(self):
        stream=io.BytesIO();write_message(stream,{'title':'Тест'});stream.seek(0);self.assertEqual(read_message(stream),{'title':'Тест'})
        for data in (struct.pack('=I',MAX_MESSAGE+1),struct.pack('=I',0),struct.pack('=I',8)+b'{}',b'\x02',struct.pack('=I',2)+b'[]'):
            with self.subTest(data=data),self.assertRaises((ValueError,EOFError)):read_message(io.BytesIO(data))
    def test_bridge_auth_and_native_process(self):
        received=[]
        def handler(message):received.append(message);return {'ok':True,'locked':True}
        bridge=BridgeServer(self.directory,handler);self.addCleanup(bridge.close)
        descriptor=json.loads(bridge.path.read_text())
        if os.name != 'nt': self.assertEqual(bridge.path.stat().st_mode&0o777,0o600)
        with socket.create_connection(('127.0.0.1',descriptor['port'])) as sock:
            sock.settimeout(2);stream=sock.makefile('rwb');write_message(stream,{'token':'wrong','message':{'action':'status'}});self.assertIsNone(read_message(stream))
        self.assertEqual(received,[])
        request=io.BytesIO();write_message(request,{'action':'status'})
        command=[os.environ['VAULT_TEST_NATIVE_HOST']] if os.environ.get('VAULT_TEST_NATIVE_HOST') else [sys.executable,'native_host_entry.py']
        process=subprocess.Popen(command+[f'chrome-extension://{EXTENSION_ID}/'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'VAULT_DATA_DIR':str(self.directory)})
        result=[]
        thread=threading.Thread(target=lambda:result.append(process.communicate(request.getvalue(),timeout=8)));thread.start()
        deadline=time.monotonic()+10
        while thread.is_alive() and time.monotonic()<deadline:self.app.processEvents();time.sleep(.005)
        thread.join(1);self.assertFalse(thread.is_alive());self.assertEqual(process.returncode,0)
        output,stderr=result[0];self.assertEqual(stderr,b'');self.assertEqual(read_message(io.BytesIO(output)),{'ok':True,'locked':True})
        self.assertEqual(received,[{'action':'status'}])
        wrong=subprocess.run([sys.executable,'native_host_entry.py','chrome-extension://'+'a'*32+'/'],input=request.getvalue(),capture_output=True,env={**os.environ,'VAULT_DATA_DIR':str(self.directory)})
        self.assertEqual(wrong.returncode,1);self.assertEqual(wrong.stdout,b'')
    def test_registration_uses_exact_extension(self):
        path=register_chrome(directory=self.directory,manifest_directory=self.directory/'manifests')
        data=json.loads(path.read_text());self.assertEqual(data['allowed_origins'],[f'chrome-extension://{EXTENSION_ID}/']);self.assertTrue(Path(data['path']).is_file())
        with self.assertRaises(ValueError):register_chrome('../bad',directory=self.directory)
    def test_controller_denies_locked_wrong_origin_and_unapproved(self):
        controller=SessionController(self.repo,Appearance(),self.app);self.addCleanup(controller.shutdown)
        self.assertFalse(controller.browser_request({'action':'fill','origin':'https://example.com','id':'a'})['ok'])
        controller.vault=self.vault;entry=PasswordEntry('Demo','u','secret',url='https://example.com');self.vault.save(entry)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No):
            self.assertFalse(controller.browser_request({'action':'list','origin':entry.url})['ok'])
        controller.approved_origins={'https://example.com','https://evil.test'}
        self.assertNotIn('password',controller.browser_request({'action':'list','origin':entry.url})['entries'][0])
        self.assertFalse(controller.browser_request({'action':'fill','origin':'https://evil.test','id':entry.id})['ok'])
        self.assertEqual(controller.browser_request({'action':'fill','origin':entry.url,'id':entry.id})['password'],'secret')
    def test_idle_clears_vault_and_approvals(self):
        controller=SessionController(self.repo,Appearance(),self.app);self.addCleanup(controller.shutdown)
        controller.vault=self.vault;controller.approved_origins.add('https://example.com');controller.last_activity=time.time()-10000
        with patch('ui.session.QTimer.singleShot') as schedule:controller.check_idle()
        self.assertIsNone(controller.vault);self.assertTrue(self.vault.locked);self.assertEqual(controller.approved_origins,set());schedule.assert_called_once()

    def test_ambiguous_origins_fail_closed(self):
        for value in ('https://example.com:0', 'https://@example.com', 'https://faß.de', 'https://exam\nple.com', 'https://example.com\t', 'https://example.com.'):
            with self.subTest(value=value),self.assertRaises(ValueError):canonical_origin(value)
        self.assertEqual(canonical_origin('https://xn--fa-hia.de/path'),'https://xn--fa-hia.de')
        self.assertNotEqual(canonical_origin('https://xn--fa-hia.de'),canonical_origin('https://fass.de'))
        self.assertEqual(canonical_origin('https://[0:0:0:0:0:0:0:1]:443/a'),'https://[::1]')

    def test_site_approval_cannot_cross_sessions(self):
        controller=SessionController(self.repo,Appearance(),self.app);self.addCleanup(controller.shutdown)
        controller.vault=self.vault
        replacement=Vault(self.repo,self.master,[])
        def switch(*args):
            controller.vault=replacement
            return QMessageBox.StandardButton.Yes
        with patch.object(QMessageBox,'question',side_effect=switch):
            self.assertFalse(controller.browser_request({'action':'list','origin':'https://example.com'})['ok'])
        self.assertEqual(controller.approved_origins,set())

    def test_browser_update_retains_android_binding(self):
        controller=SessionController(self.repo,Appearance(),self.app);self.addCleanup(controller.shutdown)
        controller.vault=self.vault;controller.window=Mock();controller.approved_origins.add('https://example.com')
        entry=PasswordEntry('Demo','u','old',url='https://example.com',app_package='com.example.app',app_signature='a'*64)
        self.vault.save(entry)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes):
            self.assertTrue(controller.browser_request({'action':'save','origin':entry.url,'username':'u','password':'new','title':'Demo'})['ok'])
        updated=self.vault.get(entry.id)
        self.assertEqual((updated.password,updated.app_package,updated.app_signature),('new','com.example.app','a'*64))
