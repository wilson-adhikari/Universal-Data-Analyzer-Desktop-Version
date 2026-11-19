import io
import json
import urllib.error

import pytest

import licensing
from licensing import LicenceError, verify

KEY = "6F0E4C97-B72A4E69-A11BF6C4-AF6517E7"
ACTIVE = (200, {"valid": True, "product": "uda-desktop", "exp": None})
INACTIVE = (200, {"valid": False, "product": None, "exp": None})


class _Reply(io.BytesIO):
    status = 200


def serve(monkeypatch, answer):
    """Replace the network: answer(key) returns (HTTP status, JSON reply) like /api/licence/validate, or raises."""
    sent = []

    def urlopen(req, timeout):
        key = json.loads(req.data)["key"]
        sent.append((req.full_url, key, timeout))
        status, reply = answer(key)
        body = json.dumps(reply).encode()
        if status != 200:
            raise urllib.error.HTTPError(req.full_url, status, "error", None, io.BytesIO(body))
        return _Reply(body)

    monkeypatch.setattr(licensing.urllib.request, "urlopen", urlopen)
    return sent


def test_active_licence_for_uda(monkeypatch):
    sent = serve(monkeypatch, lambda key: ACTIVE)
    assert verify(f"  {KEY}\n") == {"product": "uda-desktop", "exp": None}
    assert sent == [(licensing.LICENCE_URL, KEY, 15)]


@pytest.mark.parametrize(
    "answer, message",
    [
        ((200, {"valid": True, "product": "cpu-lab", "exp": None}), "different product"),
        (INACTIVE, "not active"),
        ((404, {"error": "Billing is not enabled"}), "not on sale"),
        ((503, {"error": "licence check unavailable"}), "unavailable"),
    ],
)
def test_server_answers_that_refuse(monkeypatch, answer, message):
    serve(monkeypatch, lambda key: answer)
    with pytest.raises(LicenceError, match=message):
        verify(KEY)


def test_offline_is_a_clear_error(monkeypatch):
    def offline(key):
        raise urllib.error.URLError("no route")

    serve(monkeypatch, offline)
    with pytest.raises(LicenceError, match="could not reach"):
        verify(KEY)


@pytest.mark.parametrize("bad", ["", "abc", "a.b.c", "!!!.???", "x" * 100, "../../admin"])
def test_malformed_keys_are_never_sent(monkeypatch, bad):
    sent = serve(monkeypatch, lambda key: ACTIVE)
    with pytest.raises(LicenceError, match="not a licence key"):
        verify(bad)
    assert sent == []


def test_server_url_must_be_https(monkeypatch):
    sent = serve(monkeypatch, lambda key: ACTIVE)
    monkeypatch.setattr(licensing, "LICENCE_URL", "http://example.test/api/licence/validate")
    with pytest.raises(LicenceError, match="https"):
        verify(KEY)
    assert sent == []


def test_activate_saves_and_current_rechecks(tmp_path, monkeypatch):
    monkeypatch.setattr(licensing, "LICENCE_FILE", tmp_path / "UDA" / "licence.key")
    answer = {"now": ACTIVE}
    sent = serve(monkeypatch, lambda key: answer["now"])
    assert licensing.current() is None and sent == [], "no saved key: no network call"
    licensing.activate(KEY)
    assert licensing.current() == {"product": "uda-desktop", "exp": None}
    assert sent[-1][2] == 5, "start-up check uses a short timeout"
    answer["now"] = INACTIVE  # e.g. the subscription was refunded
    assert licensing.current() is None


def test_main_window_activation_flow(tmp_path, monkeypatch):
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
    app = QApplication.instance() or QApplication([])  # noqa: F841
    from ui.main_window import MainWindow

    monkeypatch.setattr(licensing, "LICENCE_FILE", tmp_path / "licence.key")
    serve(monkeypatch, lambda key: ACTIVE if key == KEY else INACTIVE)
    shown = []
    monkeypatch.setattr(QMessageBox, "information", lambda *a: shown.append(a[1]))
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: shown.append(a[1]))

    w = MainWindow()
    assert "Licensed" not in w.windowTitle()
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *a, **k: ("AAAAAAAA-BBBBBBBB-CCCCCCCC-DDDDDDDD", True))
    w.activate_licence()
    assert shown[-1] == "Licence not activated" and "Licensed" not in w.windowTitle()
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *a, **k: (KEY, True))
    w.activate_licence()
    assert shown[-1] == "Licence activated" and "Licensed to you" in w.windowTitle()
    assert MainWindow().windowTitle().endswith("Licensed to you")  # remembered and re-checked on next start
