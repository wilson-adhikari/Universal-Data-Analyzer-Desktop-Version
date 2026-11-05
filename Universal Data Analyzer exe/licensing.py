"""Offline licence check. Keys are issued by the company website after a confirmed Stripe payment.

Key format: base64url(JSON payload) "." base64url(Ed25519 signature of the payload bytes).
Only the PUBLIC key ships with the app, so keys can be verified but never forged from it.
"""
import base64
import json
import os
import sys
import time
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_public_key

PRODUCT = "uda-desktop"
_BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
PUBLIC_KEY_FILE = _BASE / "licence_public_key.pem"
LICENCE_FILE = Path(os.environ.get("APPDATA") or Path.home()) / "UDA Desktop" / "licence.key"


class LicenceError(Exception):
    pass


def _b64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verify(key: str, public_key_pem: bytes | None = None, now: float | None = None) -> dict:
    parts = key.strip().split(".")
    if len(parts) != 2 or not all(parts):
        raise LicenceError("malformed licence")
    if public_key_pem is None:
        if not PUBLIC_KEY_FILE.exists():
            raise LicenceError("licence checking is not set up in this build")
        public_key_pem = PUBLIC_KEY_FILE.read_bytes()
    try:
        body, sig = _b64(parts[0]), _b64(parts[1])
        load_pem_public_key(public_key_pem).verify(sig, body)
        lic = json.loads(body)
    except (InvalidSignature, ValueError):
        raise LicenceError("invalid licence key") from None
    if lic.get("product") != PRODUCT:
        raise LicenceError("licence is for a different product")
    exp = lic.get("exp")
    if exp is not None and exp < (time.time() if now is None else now):
        raise LicenceError("licence expired")
    return lic


def activate(key: str) -> dict:
    """Verify, then save the key so it's remembered across runs."""
    lic = verify(key)
    LICENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LICENCE_FILE.write_text(key.strip(), encoding="utf-8")
    return lic


def current() -> dict | None:
    """The saved licence if it is still valid; None otherwise (missing, tampered or expired)."""
    try:
        return verify(LICENCE_FILE.read_text(encoding="utf-8"))
    except (OSError, LicenceError):
        return None
