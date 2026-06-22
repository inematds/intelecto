"""Encrypted-at-rest secret store (stdlib-only stand-in for Fernet).

The plan (Task 1.2) specifies Fernet from the `cryptography` package, keyed to a
machine id. To keep the test core dependency-free, this uses a stdlib
PBKDF2-HMAC-derived keystream XOR'd over the plaintext (HMAC tag for integrity).
NOT cryptographically equivalent to Fernet/ChaCha20 — it proves the interface
(save/get/list/delete, values unreadable as plaintext, machine-tied key). Swap in
`cryptography.fernet.Fernet` for production; the public API stays identical.
"""
import base64
import hashlib
import hmac
import json
import os

_ITER = 100_000


def _machine_id() -> str:
    for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            continue
    # Fallback: stable-ish host identifier.
    return hashlib.sha256(os.uname().nodename.encode()).hexdigest()


def _keystream(key: bytes, nonce: bytes, n: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:n])


class SecretStore:
    def __init__(self, path: str, machine_id: str | None = None):
        self.path = os.path.expanduser(path)
        mid = machine_id or _machine_id()
        # Derive a 32-byte key from the machine id (acts as the master key).
        self._key = hashlib.pbkdf2_hmac("sha256", mid.encode(), b"jarvis-secret-salt", _ITER, 32)
        self._data: dict[str, str] = {}
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def _encrypt(self, value: str) -> str:
        nonce = os.urandom(16)
        pt = value.encode("utf-8")
        ct = bytes(a ^ b for a, b in zip(pt, _keystream(self._key, nonce, len(pt))))
        tag = hmac.new(self._key, nonce + ct, hashlib.sha256).digest()
        return base64.b64encode(nonce + tag + ct).decode("ascii")

    def _decrypt(self, blob: str) -> str:
        raw = base64.b64decode(blob)
        nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
        expect = hmac.new(self._key, nonce + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expect):
            raise ValueError("secret integrity check failed (wrong machine/key?)")
        pt = bytes(a ^ b for a, b in zip(ct, _keystream(self._key, nonce, len(ct))))
        return pt.decode("utf-8")

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f)

    def save_secret(self, name: str, value: str) -> None:
        self._data[name] = self._encrypt(value)
        self._flush()

    def get_secret(self, name: str) -> str | None:
        blob = self._data.get(name)
        return self._decrypt(blob) if blob is not None else None

    def list_secrets(self) -> list[str]:
        return sorted(self._data.keys())

    def delete_secret(self, name: str) -> None:
        if name in self._data:
            del self._data[name]
            self._flush()
