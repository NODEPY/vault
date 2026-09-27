# Release status · 0.1.0-beta.2

Public beta source under MIT. See the [full verification report](TEST_REPORT.md) for results, fixes and gaps, and [installation guide](INSTALL.md) for each OS.

47 desktop tests, 7 Node tests, 14 Android tests and 10 browser fixture assertions passed locally. Python/Java encrypted-file interchange passed. Android packages build and lint completes with no errors.

macOS local packages target Apple Silicon and are ad-hoc signed without notarization. Windows/Linux builds run in GitHub Actions. Android APK is debug-signed; AAB is unsigned. No store listing exists. Real-device Android Autofill, a full installed-Chrome flow, clean-machine interactive checks and an independent security review remain outstanding.

All preview accounts and encrypted test fixtures are fictional. No personal vault or signing key belongs in this repository.
