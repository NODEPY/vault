# Verification report — Vault 0.1.0-beta.2

**Date:** 27 September 2026 · **Assessment:** suitable for a clearly labelled public beta source release, not a claim of production security.

## Results before publication

| Check | Result | Scope |
| --- | --- | --- |
| Python desktop suite | **47 passed** | Crypto, storage, UI flows, reset, settings, translation/theme consistency, generator, backup merge, origin matching, bridge authentication, session locking |
| Node policy/background suite | **7 passed** | Sender restrictions, exact-site policy, memory-only capture, navigation, expiry replacement, permission revocation |
| Android JVM/Robolectric suite | **14 passed** | Crypto, file validation, onboarding, CRUD, lock lifecycle, normalization, settings, reset, atomic recovery, rendered preview |
| Android lint | **0 errors, 1 warning** | Warning concerns a newer Android Gradle plugin version; pinned toolchain remains intentional |
| Browser DOM fixture | **10 assertions passed** | Visible field filling, capture, no submission, hidden/transparent fields, cross-origin action rejection |
| Python ↔ Java interchange | **Passed both directions** | Python fixture opened by JVM tests; Java-produced encrypted file opened by Python |
| macOS packaged app and native host | **Passed** | App smoke check, native protocol test, extracted archive signature and relocation |
| Android packages | **Built successfully** | Debug APK and unsigned production AAB |

Environment: macOS Apple Silicon, Python 3.14.7, PySide6 6.11.2, cryptography 50.0.1, JDK 17, Gradle 8.13, Android compile SDK 36, Robolectric SDK 35. All credentials are fictional and vault tests use disposable files. Personal vaults were not used.

## Findings fixed during this review

1. **Ambiguous website identity:** port 0 could collapse to the default HTTPS origin; built-in legacy IDNA conversion could interpret some Unicode names differently from browsers. The desktop and Android now reject ambiguous input and accept explicit ASCII/punycode domains. Control characters and embedded credentials are rejected. Subdomains and non-default ports remain separate. Existing entries created with Unicode addresses should be reviewed against the browser address before filling; the original Unicode spelling cannot be reconstructed from an already normalized entry.
2. **Session-bound consent:** an approval dialog must apply to the same unlocked vault instance that requested it. Changing the session while awaiting approval now cancels that request.
3. **Android associations:** updating a login through Chrome now retains its Android package/certificate binding.
4. **Candidate lifetime:** replacing a browser capture no longer lets an older timeout delete the new candidate. Revoking permission clears the affected pending capture. Expiration uses a monotonic clock.
5. **Android lifecycle:** destroying an old activity no longer removes the newer activity's lock callback.
6. **Android persistence:** saved records are validated and cloned, preserving canonical website values and preventing later caller mutations from altering the stored in-memory record.

Regression tests cover these changes. Passing tests establish these specific behaviors, not absence of all vulnerabilities.

## What was not established

- No independent security audit, penetration test, formal proof or comprehensive dependency vulnerability assessment has been performed.
- The browser fixture runs the real content script with simulated extension messaging and HTTPS location. It does not exercise a complete installed-Chrome/native-host/site flow. Standalone Chromium could not launch in this local sandbox.
- Robolectric is not a physical device or full system emulator. Real Android Autofill requests, manufacturer-specific behavior and document pickers still need device testing. The local emulator could not start.
- Windows and Linux local execution was unavailable. Their CI jobs are configured; see actual workflow runs for platform results. CI packaging alone does not establish usability on a clean end-user machine.
- macOS packages are ad-hoc signed, not notarized. Android APKs use debug signing; production AABs are unsigned. Store publication and publisher signing are unfinished.
- An unlocked compromised device, weak master password, malicious trusted website and clipboard manager remain outside Vault's protection. See [security design](SECURITY.md).

## Reproduce

```sh
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
node --test extension/tests/*.test.js
cd android
sh ./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:bundleRelease
cd ..
python scripts/check_android_interop.py
```

For actual Chromium DOM tests, install the pinned Playwright setup described in [BUILDING](BUILDING.md) and run `node extension/tests/content.cjs`. For bundle checks, build/package on the target OS and run the packaged executable with `--smoke-test`.

The repository's [Actions workflow](https://github.com/NODEPY/vault/actions/workflows/build.yml) repeats desktop checks and builds separately on macOS, Windows and Ubuntu, plus Android and Chromium jobs. Consult a specific commit's result rather than assuming the badge proves all platforms are production-ready.
