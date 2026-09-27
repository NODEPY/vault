# Security design and limits

Vault is a beta without an independent security audit. Tests verify specific behavior; they do not establish that a password manager is safe against every attack.

## File format

`VAULT1\0` (7 bytes), a 16-byte random salt, then a URL-safe Base64 Fernet token. The payload is a UTF-8 JSON array. Each entry contains `id`, `title`, `username`, `password`, and optional `url`, `app_package`, `app_signature`. Old desktop files without the optional fields remain readable.

The key is derived using Argon2id v1.3, 65,536 KiB memory, 3 iterations, 4 lanes and 32 output bytes. Fernet uses AES-128-CBC, a fresh random IV, PKCS7 padding and HMAC-SHA256 authentication. Authentication is checked before plaintext is accepted. The salt and Fernet creation timestamp are not secret. Encryption does not hide the approximate file size.

Desktop uses `cryptography`; Android uses Bouncy Castle for Argon2id and the platform Java cryptography implementation for AES/HMAC. Python→Java and Java→Python fixtures verify interoperability. Desktop keeps a derived cipher during an unlocked session rather than storing the master password on the Vault object. Android zeroes the session key byte array on lock. Python/Java strings, framework widgets and garbage collection cannot guarantee complete memory erasure.

Desktop writes use a temporary file in the same folder, flush/fsync and atomic replacement. Android uses AtomicFile. Failed writes retain the prior committed data. Files are limited to 16 MiB. Appearance settings are not encrypted; credentials, website addresses and Android application associations are inside the encrypted payload.

## Browser connection

Chrome Native Messaging exchanges native-endian 32-bit length-prefixed JSON through stdin/stdout. The host accepts only the configured extension origin. It connects to a random loopback TCP port using a per-run random 256-bit token from an owner-only session descriptor. This protocol is not an HTTP server and does not accept browser-origin requests.

The desktop app must be unlocked. Access to each HTTPS origin requires desktop confirmation once per session; saving/updating a captured password requires confirmation. On lock, approvals and decrypted entries are discarded. The extension background worker derives the origin from browser-provided tab/sender data; content scripts cannot request list/fill operations. A selected password is released only for an exact origin match and the tab origin is checked again before filling.

The extension does not encrypt or persist captured passwords. They are temporary in-memory candidates. Matching does not share credentials with sibling domains, subdomains, other ports or HTTP pages. Site JavaScript can see a password after it is filled into that site's form, as with any form fill. A malicious page at an explicitly trusted origin remains a threat.

## Android autofill

Autofill authentication uses a non-exported activity and a short-lived in-memory request token. Each request requires unlock and explicit account/app confirmation. Stored associations include the requested package and SHA-256 signing-certificate digest. A WebView's self-reported domain is not trusted, so this beta declines WebView/browser requests. Multiple ambiguous password fields are declined. The service does not automatically collect app passwords.

The app has no INTERNET permission. Android cloud/device backup is excluded; users can deliberately export encrypted backups. FLAG_SECURE blocks normal screenshots. It is not protection against rooted devices, privileged malware or a compromised OS.

## What this does not protect against

Malware running as your OS user, keyloggers, privileged screen/clipboard tools, a compromised browser/site, weak master passwords or offline guessing, memory inspection while unlocked, OS snapshots, copied backups and physical access to an unlocked device. Clipboard managers may retain copied secrets even after Vault clears its own current clipboard item. Deletion removes the application's file; it is not guaranteed physical erasure on SSDs or removal from OS/device backups.

There is no account recovery. Reset is destructive and requires typing DELETE. Keep a separate encrypted backup and remember its master password. Do not submit real passwords, master passwords or vault files in bug reports.

References: [Fernet](https://cryptography.io/en/latest/fernet/), [Argon2id](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#argon2id), [Chrome Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging), [Android Autofill](https://developer.android.com/guide/topics/text/autofill-services).
