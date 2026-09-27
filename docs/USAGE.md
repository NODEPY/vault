# Using Vault

A local password manager for macOS, Windows, Linux and Android, with a Chrome companion for desktop. English is the default; Ukrainian, Polish, German and Spanish are included. Five themes: Graphite, Paper, Dune, Pine and Ink.

**This is a first beta, not an independently audited security product.** See [release status](RELEASE_STATUS.md) for exactly what has been built and tested. There is no cloud account, telemetry, recovery service or automatic device sync.

## Use the desktop app

Extract the complete desktop archive into a permanent folder. On macOS keep `Vault.app` and `native-host` beside each other. On Windows/Linux keep `native-host` inside the `Vault` folder. Start Vault and choose a language, theme and long master passphrase. It cannot be recovered if forgotten.

The current Mac build is for Apple Silicon and is ad-hoc signed, without Apple notarization. Windows and Linux builds are configured in GitHub Actions and must be generated and tested on those systems before their release.

Add an entry with a service, username and password. Add its HTTPS website address to use Chrome filling. Use Tools to export/import an encrypted backup. Imports merge entries and retain the existing vault. The password used when exporting a backup is needed to open that backup, even after a later vault reset.

Passwords hide after 10 seconds. Copied values are cleared after 20 seconds when Vault still owns the clipboard. Desktop sessions lock after the selected idle interval. Forgotten master password → type `DELETE` removes this device's vault and lets you start again; separately saved backups remain.

## Android

Install the beta APK on Android 8.0 or later. It is a debug-signed test build with package `com.appkaui.vault.beta`; the production package is `com.appkaui.vault`. Export a `.vault` backup from desktop, transfer it yourself, and import it from Tools on the phone. Nothing is uploaded by Vault.

Tools → Enable Android autofill lets you select Vault as the system autofill service. For supported native-app login forms, unlock Vault, choose an account and confirm the target app. The record becomes associated with that app's package and signing certificate. Browser/WebView autofill and automatic capture on Android are not part of this beta. Add/edit mobile entries inside Vault.

Android locks when leaving the app, except while its own backup file picker is open (the idle lock still applies). Idle locking is five minutes. Screenshots are blocked in the application. Clipboard clearing can be delayed by Android's restrictions while the application is in the background; prefer system autofill.

## Chrome companion

1. Keep the desktop app in its final location and open it.
2. Extract `Vault-Chrome-0.1.0-beta.2.zip`. In `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select the folder containing `manifest.json`.
3. Copy the extension ID. In Vault choose **Tools → Connect Chrome**, enter that ID, and unlock the vault.
4. Open an HTTPS login page and the extension. Enable Vault for that website. Approve site access in the desktop app.
5. Select **Fill** for an existing account. To save one, sign in and then open the extension's `+` badge, or choose **Save current form** before signing in. Confirm **Save** and approve in the desktop app.

Filling is user-triggered and never submits the form. Only the exact HTTPS origin matches: subdomains and non-default ports are separate. Frames, hidden fields and forms posting to another origin are excluded. Captured credentials stay in extension memory for up to two minutes and can disappear sooner if Chrome stops the background worker. The extension has no independent vault.

See [privacy](PRIVACY.md), [security design](SECURITY.md) and [building/releasing](BUILDING.md).

