"""Unit tests for the Streamlit secrets -> os.environ bridge."""

from __future__ import annotations

import os
from unittest.mock import patch

from ui_components import secrets_bridge


class _FakeSecrets:
    """Minimal stand-in for ``st.secrets`` that supports item access."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def __getitem__(self, key: str):
        return self._data[key]


def test_push_copies_known_keys(monkeypatch) -> None:
    for key in secrets_bridge._SECRET_KEYS:
        monkeypatch.delenv(key, raising=False)

    fake_st = type("FakeSt", (), {})()
    fake_st.secrets = _FakeSecrets(
        {
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "SUPABASE_URL": "https://example.supabase.co",
            # Unknown keys are ignored
            "SOME_OTHER_KEY": "ignored",
        }
    )
    with patch.dict("sys.modules", {"streamlit": fake_st}):
        pushed = secrets_bridge.push_secrets_to_env()

    assert "ANTHROPIC_API_KEY" in pushed
    assert "SUPABASE_URL" in pushed
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test"
    assert os.environ["SUPABASE_URL"] == "https://example.supabase.co"
    # Not in secrets -> not pushed
    assert "ELEVENLABS_API_KEY" not in pushed


def test_push_does_not_overwrite_existing_env(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")

    fake_st = type("FakeSt", (), {})()
    fake_st.secrets = _FakeSecrets({"ANTHROPIC_API_KEY": "from-secrets"})
    with patch.dict("sys.modules", {"streamlit": fake_st}):
        pushed = secrets_bridge.push_secrets_to_env()

    assert "ANTHROPIC_API_KEY" not in pushed
    assert os.environ["ANTHROPIC_API_KEY"] == "from-env"


def test_push_is_a_noop_without_streamlit(monkeypatch) -> None:
    # Make ``import streamlit`` fail inside the bridge.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("no streamlit")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        pushed = secrets_bridge.push_secrets_to_env()

    assert pushed == []


def test_push_is_idempotent(monkeypatch) -> None:
    for key in secrets_bridge._SECRET_KEYS:
        monkeypatch.delenv(key, raising=False)

    fake_st = type("FakeSt", (), {})()
    fake_st.secrets = _FakeSecrets({"ANTHROPIC_API_KEY": "sk-ant-test"})

    with patch.dict("sys.modules", {"streamlit": fake_st}):
        first = secrets_bridge.push_secrets_to_env()
        second = secrets_bridge.push_secrets_to_env()

    assert first == ["ANTHROPIC_API_KEY"]
    # Second call finds the value already in os.environ and skips.
    assert second == []
