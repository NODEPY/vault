# Build and release

## Desktop

Install `requirements-build.txt` in a virtual environment, then run:

```sh
python scripts/build_desktop.py
python scripts/package_desktop.py
```

Build on the target OS. PyInstaller does not cross-compile Windows/Linux binaries from macOS. GitHub Actions has separate macOS, Windows and Ubuntu jobs. Test the resulting package on a clean supported machine before publishing it. `.tar.gz` preserves executable permissions and Mac framework symlinks; Windows uses ZIP.

Keep the native-host directory alongside the app as described in README. Moving the app later requires running Tools → Connect Chrome again. To remove Chrome integration, remove `com.appkaui.vault.json` from Chrome's user NativeMessagingHosts directory; on Windows also remove its HKCU native host registration. The vault remains intact.

The generated Mac binary is ad-hoc signed. To distribute with standard Gatekeeper trust, the publisher needs their own Apple Developer ID, signs all nested binaries and the bundle, notarizes the archive with Apple's tools and staples the ticket. Do not bundle private signing keys. Windows publisher signing and clean-machine validation are also publisher release steps.

## Android

Use JDK 17, Android SDK platform 36 and the included Gradle 8.13 wrapper:

```sh
cd android
./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:bundleRelease
cd ..
python scripts/check_android_interop.py
```

`app-debug.apk` is installable and debug-signed, for testing only. `app-release.aab` is an unsigned production bundle. Configure the owner's upload key in a local/private Gradle signing configuration or CI secrets before making a Play release. Preserve the signing key securely for updates; do not commit it or include it in downloadable archives. Debug and production package IDs differ.

Use Android Studio or a device to exercise first-run setup, reset, add/edit/delete, backup export/import, lock on background, keyboard layouts and a real native-app autofill request. Robolectric tests cover basic screen flows without a device; they do not replace real-device autofill validation.

## Chrome

Load `extension/` unpacked for local testing. The checked-in public manifest key gives a stable development ID; it is not a secret signing key. A Chrome Web Store item can have a different assigned ID. Update the configured ID through Tools → Connect Chrome after installing the store version.

Run Node tests and the Playwright form fixture:

```sh
node --test extension/tests/*.test.js
npm install --no-save playwright@1.56.1
npx playwright install chromium
node extension/tests/content.cjs
```

For a store submission, include only manifest, JS/HTML/CSS and icons, supply actual screenshots, explain nativeMessaging/per-site permissions, and publish the real privacy notice under the publisher's account. Do not claim compatibility with every login page; cross-origin forms, frames and WebViews are intentionally outside this beta's fill behavior.

## Publisher-owned finishing steps

Original project code uses MIT; store identities, signing keys and contact channels remain publisher-owned. Before a public stable release: validate Windows/Linux artifacts, complete real-device Android and installed-Chrome integration testing, obtain an independent security review, and configure official signing. The beta packages and source snapshot make those steps concrete; store listings are not part of this beta.
