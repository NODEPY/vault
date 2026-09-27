# Contributing

Small, focused fixes and test cases are welcome. Open an issue for major changes before implementing them. Use fictional credentials and temporary directories; never attach your actual vault.

Install `requirements.txt`, then run:

```sh
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
node --test extension/tests/*.test.js
```

See [BUILDING](docs/BUILDING.md) for Android, browser DOM tests and packaged builds. Include the OS, reproduction steps and relevant test results in pull requests. Keep translations in all five languages aligned. Changes to the encrypted format must preserve or explicitly migrate desktop/Android compatibility.

Describe verified behavior and limitations accurately. Read [SECURITY.md](SECURITY.md) before reporting security issues. Contributions to original project code are under the repository's MIT license; retain third-party notices.
