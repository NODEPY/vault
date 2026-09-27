# Install Vault

[← Back to Vault](../README.md)

Use a supported OS and current security updates. The desktop source requires Python 3.11+ (CI uses 3.14). The pinned Qt wheels determine the exact OS/architecture compatibility. Current macOS wheels require macOS 13+. Android requires Android 8.0/API 26 or later. These are beta builds; start with test credentials.

## macOS

### From source

Install Python 3.11+ from [python.org](https://www.python.org/downloads/macos/). Download this repository using **Code → Download ZIP**, extract it and open Terminal in that folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

For later launches, open the project folder, activate `.venv` and run `python main.py` again. If `python` is not found, the environment has not been activated; use `python3` to create it.

### Packaged build

When a macOS archive is attached to a [release](https://github.com/NODEPY/vault/releases), choose your CPU architecture, extract it fully and keep `Vault.app` beside `native-host` in a permanent folder. Open `Vault.app`. The locally built package is Apple Silicon (`arm64`), ad-hoc signed and not notarized. macOS may block it as an unidentified developer; inspect the source and build locally if you do not want to approve that package. Do not disable Gatekeeper globally. Intel Macs require a separate build on a compatible Intel Mac.

## Windows

Install a supported 64-bit Python 3.11+ from [python.org](https://www.python.org/downloads/windows/), including the Python launcher. Download and extract the repository. Open PowerShell in the extracted folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Directly using the environment's Python avoids PowerShell activation-policy changes. For a packaged build, open a successful **Test and build beta** Actions run, download `Vault-windows-latest`, extract the artifact and then its contained ZIP. Run `Vault.exe` from the complete `Vault` folder; keep `_internal` and `native-host` with it. No official Windows publisher signature is supplied. Interactive Windows validation remains a release requirement.

## Linux

On a current Ubuntu desktop, install Python and the Qt runtime libraries:

```sh
sudo apt-get update
sudo apt-get install python3 python3-venv libegl1 libopengl0 libxcb-cursor0 libxkbcommon-x11-0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Run these commands from the extracted repository folder after installing the packages. On other distributions use their equivalent system packages. A graphical desktop session is required.

For a packaged Ubuntu build, download `Vault-ubuntu-24.04` from a successful Actions run. Extract the artifact and its `.tar.gz` file. From the extracted top-level `Vault` folder run `./Vault/Vault`. Keep the directory structure intact. The bundle is built on Ubuntu 24.04 and is not promised to work on distributions with older system libraries.

## Android

### Test APK

Download a debug APK from a release or the `Vault-Android-beta` artifact of a successful Actions run. Transfer it to your phone, open it and grant your chosen installer permission to install that APK if Android asks. The package is `com.appkaui.vault.beta`; it is a **debug-signed test build**. Different machines/CI runs may use different debug signing keys, so updating an existing test installation may fail. Export an encrypted backup before uninstalling; uninstalling removes local app data.

The `.aab` file is an unsigned publishing bundle, not an installable APK. There is no Google Play listing yet.

### Build yourself

Install Android Studio and JDK 17. Open the repository's `android` folder in Android Studio, install SDK platform 36 when prompted, let Gradle sync, choose a device and run the `app` configuration. Or use the included wrapper with your SDK configured:

```sh
cd android
./gradlew :app:assembleDebug
```

On Windows use `gradlew.bat :app:assembleDebug`. The APK is at `app/build/outputs/apk/debug/app-debug.apk`.

### Transfer and autofill

Create your vault, then use Tools to import an encrypted desktop backup. Enter the master passphrase used for that backup; it can differ from the phone vault's passphrase. There is no automatic synchronization. Export/import deliberately when moving changes between devices.

Use **Tools → Enable Android autofill**, select Vault in Android settings, then try a supported native-app login form. Unlock, choose an account and confirm the app. Browser/WebView forms and automatic Android password capture are not implemented. Real-device autofill testing is still outstanding.

## Chrome

This guide applies to Chrome on macOS, Windows and Linux; it does not install a Safari extension.

1. Place and open the desktop application in its permanent location.
2. Open `chrome://extensions`, enable Developer mode and choose **Load unpacked**. Select this repository's `extension` folder, or the extracted companion ZIP's folder containing `manifest.json`.
3. Copy the displayed extension ID. In Vault choose **Tools → Connect Chrome**, paste the ID and unlock Vault.
4. Visit an HTTPS login page, open Vault Companion and enable it for that site. Approve access in desktop Vault.
5. Select an account to fill. To save, capture the visible form or use the `+` badge after sign-in, then confirm in the popup and desktop app.

If Chrome reports a missing native host, reopen Vault and repeat Connect Chrome after moving the installation. Origin matching includes the port and subdomain. For internationalized website addresses entered manually in Vault, use the browser's ASCII/punycode hostname (`xn--…`); ambiguous Unicode hostnames are rejected. Embedded frames, hidden fields and forms submitting to a different origin are declined.

## First launch and backups

Choose a language and theme, then a long, unique master passphrase. This unlocks your local vault, not a remote account. Keep a separate encrypted backup before major updates. **Forgotten passphrase → reset → DELETE** permanently removes the current local vault; it does not recover old entries or erase independently saved backups.

See [usage](USAGE.md), [privacy](PRIVACY.md) and [security limitations](SECURITY.md).
