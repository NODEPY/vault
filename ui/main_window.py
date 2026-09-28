from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QAction, QFontDatabase
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget, QFileDialog, QInputDialog, QMenu,
)
from core.vault import Vault, VaultLockedError
from ui.appearance import Appearance
from ui.clipboard import clipboard_guard
from ui.entry_delegate import EntryDelegate
from ui.entry_dialog import EntryDialog
from ui.generator_dialog import GeneratorDialog
from ui.icons import icon
from ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    lockRequested = Signal()
    closed = Signal()
    def __init__(self, vault: Vault, appearance=None):
        super().__init__()
        self.vault = vault
        self.appearance = appearance or Appearance()
        self.resize(1080, 700)
        self.setMinimumSize(940, 600)
        self.selected_id = None
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_password)
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(lambda: self.copy_status.clear())
        container = QWidget()
        self.setCentralWidget(container)
        root = QHBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        self.sidebar = sidebar
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(192)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(14, 30, 14, 20)
        nav.setSpacing(10)
        wordmark = QLabel('Vault')
        wordmark.setObjectName('wordmark')
        wordmark.setContentsMargins(12, 0, 0, 24)
        nav.addWidget(wordmark)
        self.library_label = QLabel()
        self.library_label.setObjectName('sectionLabel')
        self.library_label.setContentsMargins(12, 10, 0, 8)
        nav.addWidget(self.library_label)
        self.all_button = QPushButton()
        self.all_button.setObjectName('nav')
        self.all_button.setCheckable(True)
        self.all_button.setChecked(True)
        self.all_button.clicked.connect(self.show_all)
        nav.addWidget(self.all_button)
        self.generator_button = QPushButton()
        self.generator_button.setObjectName('nav')
        self.generator_button.clicked.connect(self.open_generator)
        nav.addWidget(self.generator_button)
        nav.addStretch()
        self.tools_button = QPushButton()
        self.tools_button.setObjectName('nav')
        self.tools_menu = QMenu(self)
        self.tool_actions = {}
        for key, callback in [('export_backup',self.export_backup),('import_backup',self.import_backup),('connect_chrome',self.connect_chrome),('about',self.about)]:
            action = self.tools_menu.addAction('')
            action.triggered.connect(callback)
            self.tool_actions[key] = action
        self.tools_button.setMenu(self.tools_menu)
        nav.addWidget(self.tools_button)
        self.lock_button = QPushButton()
        self.lock_button.setObjectName('nav')
        self.lock_button.clicked.connect(self.lockRequested.emit)
        nav.addWidget(self.lock_button)
        self.settings_button = QPushButton()
        self.settings_button.setObjectName('nav')
        self.settings_button.clicked.connect(self.open_settings)
        nav.addWidget(self.settings_button)
        self.local_label = QLabel()
        self.local_label.setObjectName('hint')
        self.local_label.setContentsMargins(12, 12, 0, 0)
        nav.addWidget(self.local_label)
        root.addWidget(sidebar)

        list_pane = QFrame()
        list_pane.setObjectName('listPane')
        list_pane.setFixedWidth(330)
        list_layout = QVBoxLayout(list_pane)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        list_header = QWidget()
        header_layout = QVBoxLayout(list_header)
        header_layout.setContentsMargins(22, 28, 22, 16)
        header_layout.setSpacing(14)
        self.title = QLabel()
        self.title.setObjectName('title')
        title_row = QHBoxLayout()
        title_row.addWidget(self.title, 1)
        header_layout.addLayout(title_row)
        self.counter = QLabel()
        self.counter.setObjectName('countBadge')
        title_row.addWidget(self.counter)
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search_action = self.search.addAction(icon('search', self.appearance.colors['muted']), QLineEdit.ActionPosition.LeadingPosition)
        header_layout.addWidget(self.search)
        list_layout.addWidget(list_header)
        self.entries = QListWidget()
        self.entries.setObjectName('entryList')
        self.entries.setMouseTracking(True)
        self.entries.setItemDelegate(EntryDelegate(self.appearance, self.entries))
        list_layout.addWidget(self.entries, 1)
        self.add_button = QPushButton()
        add_wrap = QHBoxLayout()
        add_wrap.setContentsMargins(20, 16, 20, 20)
        add_wrap.addWidget(self.add_button)
        list_layout.addLayout(add_wrap)
        root.addWidget(list_pane)

        details = QFrame()
        details.setObjectName('detailPane')
        detail_layout = QVBoxLayout(details)
        detail_layout.setContentsMargins(36, 28, 36, 22)
        detail_layout.setSpacing(20)
        top = QHBoxLayout()
        self.detail_section = QLabel()
        self.detail_section.setObjectName('sectionLabel')
        top.addWidget(self.detail_section, 1)
        self.edit_button = QPushButton()
        self.edit_button.setObjectName('secondary')
        self.edit_button.clicked.connect(self.edit_selected)
        top.addWidget(self.edit_button)
        self.delete_button = QPushButton()
        self.delete_button.setObjectName('quietDanger')
        self.delete_button.clicked.connect(self.delete_selected)
        top.addWidget(self.delete_button)
        detail_layout.addLayout(top)
        self.stack = QStackedWidget()
        self.stack.setObjectName("detailsStack")
        self.empty_page = QWidget()
        self.empty_page.setObjectName("detailContent")
        empty_layout = QVBoxLayout(self.empty_page)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.addStretch()
        self.empty_title = QLabel()
        self.empty_title.setObjectName('title')
        self.empty_text = QLabel()
        self.empty_text.setObjectName('subtitle')
        self.empty_text.setWordWrap(True)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_text)
        empty_layout.addStretch()
        self.stack.addWidget(self.empty_page)
        self.entry_page = QWidget()
        self.entry_page.setObjectName("detailContent")
        entry_layout = QVBoxLayout(self.entry_page)
        entry_layout.setContentsMargins(0, 26, 0, 0)
        entry_layout.setSpacing(14)
        self.avatar = QLabel()
        self.avatar.setObjectName('avatar')
        self.avatar.setFixedSize(56, 56)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        identity = QHBoxLayout()
        identity.setSpacing(16)
        identity.addWidget(self.avatar)
        names = QVBoxLayout()
        names.setSpacing(4)
        identity.addLayout(names, 1)
        entry_layout.addLayout(identity)
        self.detail_title = QLabel()
        self.detail_title.setObjectName('detailTitle')
        self.detail_title.setTextFormat(Qt.TextFormat.PlainText)
        self.detail_title.setWordWrap(True)
        self.detail_title.setMaximumHeight(108)
        names.addWidget(self.detail_title)
        self.website = QLabel()
        self.website.setObjectName("website")
        self.website.setTextFormat(Qt.TextFormat.PlainText)
        self.website.setWordWrap(True)
        names.addWidget(self.website)
        self.credentials_heading = QLabel()
        self.credentials_heading.setObjectName("credentialHeading")
        entry_layout.addWidget(self.credentials_heading)
        self.username_label, self.username_value, self.copy_username_button = self.make_field(entry_layout)
        self.password_label, self.password_value, self.copy_password_button = self.make_field(entry_layout)
        self.password_value.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_value.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        actions = QHBoxLayout()
        self.reveal_button = QPushButton()
        self.reveal_button.setObjectName('secondary')
        self.reveal_button.clicked.connect(self.toggle_password)
        actions.addWidget(self.reveal_button)
        actions.addStretch()
        entry_layout.addLayout(actions)
        self.copy_status = QLabel()
        self.copy_status.setObjectName('hint')
        self.copy_status.setWordWrap(True)
        entry_layout.addWidget(self.copy_status)
        entry_layout.addStretch()
        self.stack.addWidget(self.entry_page)
        detail_layout.addWidget(self.stack, 1)
        self.hint = QLabel()
        self.hint.setObjectName('hint')
        self.hint.setWordWrap(True)
        self.hint.setToolTip(str(self.vault.repository.path))
        detail_layout.addWidget(self.hint)
        root.addWidget(details, 1)

        self.search.textChanged.connect(self.refresh_entries)
        self.entries.currentItemChanged.connect(self.show_selected)
        self.entries.itemDoubleClicked.connect(self.edit_entry)
        self.add_button.clicked.connect(self.add_entry)
        self.copy_username_button.clicked.connect(lambda: self.copy_selected('username'))
        self.copy_password_button.clicked.connect(lambda: self.copy_selected('password'))
        self.shortcuts = []
        for key, callback in ((QKeySequence.StandardKey.Find, self.search.setFocus), (QKeySequence.StandardKey.New, self.add_entry)):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)
        self.retranslate()

    def make_field(self, layout):
        group = QFrame()
        group.setObjectName('fieldGroup')
        row = QHBoxLayout(group)
        row.setContentsMargins(18, 15, 12, 15)
        text = QVBoxLayout()
        text.setSpacing(7)
        label = QLabel()
        label.setObjectName('fieldLabel')
        value = QLineEdit()
        value.setObjectName('readField')
        value.setReadOnly(True)
        text.addWidget(label)
        text.addWidget(value)
        row.addLayout(text, 1)
        button = QPushButton()
        button.setObjectName('iconButton')
        row.addWidget(button)
        layout.addWidget(group)
        return label, value, button

    def retranslate(self):
        tr, colors = self.appearance.tr, self.appearance.colors
        self.setWindowTitle(tr('app_title'))
        self.title.setText(tr('passwords'))
        self.library_label.setText(tr('library').upper())
        self.all_button.setText(tr('all_entries'))
        self.generator_button.setText(tr('generator'))
        self.settings_button.setText(tr('settings'))
        self.tools_button.setText(tr('tools'))
        self.lock_button.setText(tr('lock'))
        self.lock_button.setIcon(icon('lock', colors['fg']))
        self.delete_button.setText(tr('delete'))
        for key, action in self.tool_actions.items(): action.setText(tr(key))
        self.local_label.setText(tr('local_vault'))
        self.search.setPlaceholderText(tr('search'))
        self.add_button.setText(tr('add').lstrip('+ '))
        self.detail_section.setText(tr('details'))
        self.credentials_heading.setText(tr('credentials'))
        self.search_action.setIcon(icon('search', colors['muted']))
        self.edit_button.setText(tr('edit'))
        self.empty_title.setText(tr('select_entry'))
        self.empty_text.setText(tr('select_hint'))
        self.username_label.setText(tr('username'))
        self.password_label.setText(tr('password'))
        self.copy_username_button.setToolTip(tr('copy_username'))
        self.copy_username_button.setAccessibleName(tr('copy_username'))
        self.copy_password_button.setToolTip(tr('copy_password'))
        self.copy_password_button.setAccessibleName(tr('copy_password'))
        self.reveal_button.setToolTip(tr('security_note'))
        self.hint.setText(tr('saved_hint'))
        for button, name in [(self.all_button,'key'),(self.generator_button,'dice'),(self.settings_button,'settings'),(self.edit_button,'edit'),(self.copy_username_button,'copy'),(self.copy_password_button,'copy'),(self.reveal_button,'eye')]:
            button.setIcon(icon(name, colors['fg']))
        self.add_button.setIcon(icon('plus', colors['button_text']))
        self.sidebar.setFixedWidth(max(192, max(button.sizeHint().width() for button in (self.all_button, self.generator_button, self.settings_button, self.tools_button, self.lock_button)) + 32))
        self.hide_password()
        self.refresh_entries()

    def show_all(self):
        self.all_button.setChecked(True)
        self.search.clear()

    def open_settings(self):
        self.hide_password()
        dialog = SettingsDialog(self.appearance, self)
        dialog.exec()
        dialog.deleteLater()
        if not self.vault.locked: self.retranslate()

    def open_generator(self):
        self.hide_password()
        dialog = GeneratorDialog(self.appearance, self)
        dialog.exec()
        dialog.deleteLater()

    def refresh_entries(self, _text=None):
        if self.vault.locked: return
        selected_id = self.selected_id
        self.entries.blockSignals(True)
        self.entries.clear()
        results = self.vault.search(self.search.text())
        selected = None
        for entry in results:
            username = entry.username or self.appearance.tr('no_username')
            item = QListWidgetItem(f'{entry.title}\n{username}')
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, (entry.title, username))
            self.entries.addItem(item)
            if entry.id == selected_id: selected = item
        if results:
            self.entries.setCurrentItem(selected or self.entries.item(0))
        self.entries.blockSignals(False)
        self.counter.setText(str(len(results)))
        self.counter.setAccessibleName(self.appearance.tr('entry_total', count=len(results)))
        self.counter.setToolTip(self.appearance.tr('entry_total', count=len(results)))
        self.show_selected(self.entries.currentItem())

    def show_selected(self, item, previous=None):
        self.hide_password()
        self.copy_status.clear()
        self.edit_button.setEnabled(item is not None)
        self.delete_button.setEnabled(item is not None)
        if item is None:
            self.selected_id = None
            self.username_value.clear()
            self.password_value.clear()
            self.website.clear()
            self.stack.setCurrentWidget(self.empty_page)
            self.empty_text.setText(self.appearance.tr('no_results' if self.search.text().strip() else 'empty'))
            return
        self.selected_id = item.data(Qt.ItemDataRole.UserRole)
        entry = self.vault.get(self.selected_id)
        self.avatar.setText(entry.title[:1].upper())
        self.website.setText(entry.url.removeprefix('https://') or self.appearance.tr('local_entry'))
        self.detail_title.setText(entry.title)
        self.username_value.setText(entry.username)
        self.password_value.setText(entry.password)
        self.stack.setCurrentWidget(self.entry_page)

    def hide_password(self):
        self.hide_timer.stop()
        self.password_value.setEchoMode(QLineEdit.EchoMode.Password)
        self.reveal_button.setText(self.appearance.tr('reveal'))

    def toggle_password(self):
        if not self.selected_id: return
        if self.password_value.echoMode() == QLineEdit.EchoMode.Password:
            self.password_value.setEchoMode(QLineEdit.EchoMode.Normal)
            self.reveal_button.setText(self.appearance.tr('hide'))
            self.hide_timer.start(10000)
        else: self.hide_password()

    def copy_selected(self, field):
        if self.selected_id is None: return
        entry = self.vault.get(self.selected_id)
        clipboard_guard().copy(getattr(entry, field))
        self.copy_status.setText(self.appearance.tr('copied'))
        self.status_timer.start(20000)

    def add_entry(self):
        dialog = EntryDialog(self, appearance=self.appearance)
        if self.save_dialog(dialog):
            self.search.clear()
            self.refresh_entries()
        dialog.deleteLater()

    def edit_selected(self):
        item = self.entries.currentItem()
        if item: self.edit_entry(item)

    def edit_entry(self, item):
        self.hide_password()
        dialog = EntryDialog(self, self.vault.get(item.data(Qt.ItemDataRole.UserRole)), self.appearance)
        if self.save_dialog(dialog): self.refresh_entries()
        dialog.deleteLater()

    def save_dialog(self, dialog):
        while dialog.exec() == QDialog.DialogCode.Accepted:
            if self.vault.locked: return False
            try:
                entry = dialog.get_entry()
                self.vault.save(entry)
                self.selected_id = entry.id
            except (OSError, ValueError):
                QMessageBox.critical(self, self.appearance.tr('save_failed'), self.appearance.tr('save_failed_body'))
                continue
            return True
        return False

    def closeEvent(self, event):
        self.hide_password()
        clipboard_guard().clear_owned()
        self.closed.emit()
        super().closeEvent(event)

    def delete_selected(self):
        if self.selected_id is None: return
        answer = QMessageBox.question(self, self.appearance.tr('delete'), self.appearance.tr('delete_entry_body'), QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes or self.vault.locked: return
        try:
            self.vault.delete(self.selected_id)
        except OSError:
            QMessageBox.critical(self, self.appearance.tr('error'), self.appearance.tr('save_failed'))
            return
        self.selected_id = None
        self.refresh_entries()

    def export_backup(self):
        import os, tempfile
        from pathlib import Path
        path, _ = QFileDialog.getSaveFileName(self, self.appearance.tr('export_backup'), 'Vault-backup.vault', 'Vault (*.vault)')
        if not path or self.vault.locked: return
        target = Path(path)
        if target.resolve() == self.vault.repository.path.resolve(): return
        try:
            data = self.vault.repository.path.read_bytes()
            fd, temporary = tempfile.mkstemp(dir=target.parent, prefix='.vault-backup-')
            try:
                with os.fdopen(fd,'wb') as file:
                    file.write(data); file.flush(); os.fsync(file.fileno())
                os.replace(temporary,target)
            finally: Path(temporary).unlink(missing_ok=True)
            QMessageBox.information(self,self.appearance.tr('export_backup'),self.appearance.tr('backup_saved'))
        except OSError:
            QMessageBox.critical(self,self.appearance.tr('error'),self.appearance.tr('save_failed'))

    def import_backup(self):
        from pathlib import Path
        from storage.repository import VaultRepository, VaultFormatError
        from core.security import VaultUnlockError
        path, _ = QFileDialog.getOpenFileName(self,self.appearance.tr('import_backup'),'','Vault (*.vault *.bin)')
        if not path or self.vault.locked: return
        password, ok = QInputDialog.getText(self,self.appearance.tr('import_backup'),self.appearance.tr('backup_password'),QLineEdit.EchoMode.Password)
        if not ok or self.vault.locked: return
        try:
            entries = VaultRepository(Path(path)).load(password)
            count = self.vault.import_entries(entries)
            self.refresh_entries()
            QMessageBox.information(self,self.appearance.tr('import_backup'),self.appearance.tr('backup_imported', count=count))
        except (OSError,ValueError,VaultFormatError,VaultUnlockError):
            QMessageBox.critical(self,self.appearance.tr('error'),self.appearance.tr('backup_error'))

    def connect_chrome(self):
        from browser_bridge.config import EXTENSION_ID
        from browser_bridge.register import register_chrome
        value, ok = QInputDialog.getText(self,self.appearance.tr('connect_chrome'),self.appearance.tr('extension_id'),text=EXTENSION_ID)
        if not ok or self.vault.locked: return
        try:
            register_chrome(value.strip(), directory=self.vault.repository.path.parent)
            QMessageBox.information(self,self.appearance.tr('connect_chrome'),self.appearance.tr('chrome_connected'))
        except (OSError,ValueError):
            QMessageBox.critical(self,self.appearance.tr('error'),self.appearance.tr('chrome_error'))

    def about(self):
        from core.version import VERSION
        QMessageBox.information(self, 'Vault', 'Vault '+VERSION+'\n\n'+self.appearance.tr('about_body'))
