# Vault privacy notice

Vault stores passwords and account information in an encrypted file on your device. Language, theme and idle-time preferences are stored separately. Vault does not operate a server, create an online account, send telemetry, include advertisements, sell data or provide automatic cloud sync.

The desktop Chrome extension reads visible login fields only on HTTPS sites where you enable it. It temporarily holds a candidate username/password in its background worker for up to two minutes, pending your confirmation. It communicates with your local desktop app through Chrome Native Messaging. Site permissions are stored in Chrome's local extension storage. Password candidates are not written there. Filling exposes the selected username/password to the intended webpage's form; the site controls that form.

The desktop bridge binds only to the loopback interface. A local session file contains its random access token; this token is deleted when the app closes normally. Same-user malware is outside the application's protection boundary.

Android has no network permission. Android Autofill receives form structure and application identity from the OS. It returns only the account you confirm. It declines website/WebView forms in this beta. Vault excludes its files from automatic Android backup. Exported backups are saved to the destination you select; if you choose a cloud document provider, that provider receives the encrypted backup under its own privacy policy.

You control entries, encrypted backups, and reset. Reset deletes only the active local vault. Uninstalling the extension removes its settings; it does not remove the desktop vault or exported files. Desktop uninstall does not automatically erase your data directory. Clipboard tools and system backups may retain their own copies.

The software publisher must add their public identity and support contact before submitting this notice to an app store. No support address or privacy website is invented in this beta package.
