"""Encryption utilities for storing sensitive tokens in the database."""

import os

from cryptography.fernet import Fernet

_KEY: bytes | None = None


def _get_key() -> bytes:
    global _KEY
    if _KEY is None:
        raw = os.getenv("NEXUS_ENCRYPTION_KEY", "")
        if not raw:
            raise RuntimeError(
                "NEXUS_ENCRYPTION_KEY is not set. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _KEY = raw.encode() if isinstance(raw, str) else raw
    return _KEY


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string and return the ciphertext as a string."""
    f = Fernet(_get_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a ciphertext string and return the plaintext."""
    f = Fernet(_get_key())
    return f.decrypt(ciphertext.encode()).decode()
