import base64
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import licensing
from licensing import LicenceError, verify


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _keypair():
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, pub


def _sign(priv, **overrides) -> str:
    payload = {"v": 1, "product": "uda-desktop", "email": "a@b.test", "sid": "cs_test_1", "iat": 1, "exp": None, **overrides}
    body = json.dumps(payload).encode()
    return f"{_b64(body)}.{_b64(priv.sign(body))}"


def test_valid_licence_verifies():
    priv, pub = _keypair()
    assert verify(_sign(priv), pub)["email"] == "a@b.test"


def test_tampered_payload_rejected():
    priv, pub = _keypair()
    _, sig = _sign(priv).split(".")
    forged = _b64(json.dumps({"v": 1, "product": "uda-desktop", "email": "x", "sid": "s", "iat": 1, "exp": None}).encode())
    with pytest.raises(LicenceError, match="invalid"):
        verify(f"{forged}.{sig}", pub)


def test_other_key_rejected():
    priv, _ = _keypair()
    _, other_pub = _keypair()
    with pytest.raises(LicenceError, match="invalid"):
        verify(_sign(priv), other_pub)


def test_wrong_product_rejected():
    priv, pub = _keypair()
    with pytest.raises(LicenceError, match="different product"):
        verify(_sign(priv, product="other"), pub)


def test_expiry():
    priv, pub = _keypair()
    key = _sign(priv, exp=1000)
    with pytest.raises(LicenceError, match="expired"):
        verify(key, pub, now=2000)
    assert verify(key, pub, now=500)["exp"] == 1000


@pytest.mark.parametrize("bad", ["", "abc", "a.b.c", "!!!.???"])
def test_malformed_rejected(bad):
    _, pub = _keypair()
    with pytest.raises(LicenceError):
        verify(bad, pub)


def test_activate_saves_and_current_reloads(tmp_path, monkeypatch):
    priv, pub = _keypair()
    key_file = tmp_path / "pub.pem"
    key_file.write_bytes(pub)
    monkeypatch.setattr(licensing, "PUBLIC_KEY_FILE", key_file)
    monkeypatch.setattr(licensing, "LICENCE_FILE", tmp_path / "UDA" / "licence.key")
    assert licensing.current() is None
    licensing.activate(_sign(priv))
    assert licensing.current()["email"] == "a@b.test"
    (tmp_path / "UDA" / "licence.key").write_text("tampered.key")
    assert licensing.current() is None


def test_missing_public_key_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(licensing, "PUBLIC_KEY_FILE", tmp_path / "missing.pem")
    with pytest.raises(LicenceError, match="not set up"):
        verify("a.b")


def test_main_window_activation_flow(tmp_path, monkeypatch):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
    app = QApplication.instance() or QApplication([])  # noqa: F841
    from ui.main_window import MainWindow

    priv, pub = _keypair()
    (tmp_path / "pub.pem").write_bytes(pub)
    monkeypatch.setattr(licensing, "PUBLIC_KEY_FILE", tmp_path / "pub.pem")
    monkeypatch.setattr(licensing, "LICENCE_FILE", tmp_path / "licence.key")
    shown = []
    monkeypatch.setattr(QMessageBox, "information", lambda *a: shown.append(a[1]))
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: shown.append(a[1]))

    w = MainWindow()
    assert "Licensed" not in w.windowTitle()
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *a, **k: ("garbage", True))
    w.activate_licence()
    assert shown[-1] == "Licence not activated" and "Licensed" not in w.windowTitle()
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *a, **k: (_sign(priv), True))
    w.activate_licence()
    assert shown[-1] == "Licence activated" and "Licensed to a@b.test" in w.windowTitle()
    assert MainWindow().windowTitle().endswith("Licensed to a@b.test")  # remembered on next start
