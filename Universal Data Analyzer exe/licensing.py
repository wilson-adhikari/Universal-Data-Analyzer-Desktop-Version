"""Licence check for UDA Desktop, made online by the AXIOMERA licence server.

The key is the Gumroad licence key from the purchase receipt. The server asks Gumroad on every check, so a
cancelled, refunded or failed subscription stops working (the same check the CPU and GPU labs use).
"""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

PRODUCT = "uda-desktop"
LICENCE_URL = os.environ.get("UDA_LICENCE_URL") or "https://axiomera-iota.vercel.app/api/licence/validate"
LICENCE_FILE = Path(os.environ.get("APPDATA") or Path.home()) / "UDA Desktop" / "licence.key"
_KEY = re.compile(r"[A-Za-z0-9-]{8,64}")  # Gumroad keys look like 6F0E4C97-B72A4E69-A11BF6C4-AF6517E7


class LicenceError(Exception):
    pass


def _ask_server(key: str, timeout: float) -> tuple[int, dict]:
    """POST {"key": key} to the licence server; returns (HTTP status, JSON reply)."""
    if not LICENCE_URL.startswith(("https://", "http://localhost")):
        raise LicenceError("UDA_LICENCE_URL must be an https:// URL")
    req = urllib.request.Request(
        LICENCE_URL, data=json.dumps({"key": key}).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read()
    except (urllib.error.URLError, OSError):
        raise LicenceError("could not reach the licence server; check your internet connection") from None
    try:
        return status, json.loads(body or b"{}")
    except ValueError:
        return status, {}


def verify(key: str, timeout: float = 15) -> dict:
    """The licence if the server confirms the key is active for UDA Desktop; raises LicenceError otherwise."""
    key = key.strip()
    if not _KEY.fullmatch(key):
        raise LicenceError("that is not a licence key: paste the key from your Gumroad receipt")
    status, reply = _ask_server(key, timeout)
    if reply.get("error") == "Billing is not enabled":
        raise LicenceError("subscriptions are not on sale yet, so UDA Desktop needs no licence for now")
    if status != 200:
        raise LicenceError("the licence check is unavailable right now; try again later")
    if reply.get("valid") is not True:
        raise LicenceError("licence not active: check the key and that the subscription is still active")
    if reply.get("product") != PRODUCT:
        raise LicenceError("licence is for a different product")
    return {"product": PRODUCT, "exp": reply.get("exp")}


def activate(key: str) -> dict:
    """Verify, then save the key so it's remembered across runs."""
    lic = verify(key)
    LICENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LICENCE_FILE.write_text(key.strip(), encoding="utf-8")
    return lic


def current() -> dict | None:
    """The saved licence if the server still confirms it; None otherwise (missing, inactive, or offline)."""
    # shortcut: checked on the UI thread at start-up (at most 5 s when the network hangs); move it to a worker
    # once paid features depend on it.
    try:
        return verify(LICENCE_FILE.read_text(encoding="utf-8"), timeout=5)
    except (OSError, LicenceError):
        return None
