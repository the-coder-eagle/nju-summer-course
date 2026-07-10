import keyring
import pytest
from harness.auth import store


@pytest.fixture(autouse=True)
def fake_keyring(monkeypatch):
    mem = {}
    monkeypatch.setattr(keyring, "set_password", lambda s, a, v: mem.__setitem__((s, a), v))
    monkeypatch.setattr(keyring, "get_password", lambda s, a: mem.get((s, a)))
    monkeypatch.setattr(keyring, "delete_password", lambda s, a: mem.pop((s, a), None))
    return mem


def test_set_get_clear_no_echo():
    assert store.get_key() is None
    store.set_key("sk-secret")
    assert store.has_key() is True
    assert store.get_key() == "sk-secret"
    store.clear_key()
    assert store.has_key() is False
