"""Bridge Streamlit secrets into ``os.environ``.

The pipeline's :class:`pipeline.config.Config` reads from ``os.environ``
(with a ``.env`` fallback via python-dotenv). When running under
Streamlit, users typically prefer ``st.secrets`` — either
``.streamlit/secrets.toml`` locally or the Secrets tab on Streamlit
Community Cloud.

Call :func:`push_secrets_to_env` once at the top of every Streamlit entry
point (``streamlit/app.py`` and each page in ``streamlit/pages/``). It is
idempotent: values already present in ``os.environ`` are left untouched,
so a ``.env`` file continues to take precedence if the user has one.

Keys pushed:

- ``ANTHROPIC_API_KEY``
- ``ELEVENLABS_API_KEY``
- ``SUPABASE_URL``
- ``SUPABASE_ANON_KEY``
- ``SONNET_MODEL``, ``OPUS_MODEL``
- ``ELEVENLABS_MODEL``
- ``DEFAULT_HOST_VOICE``, ``DEFAULT_BULL_VOICE``, ``DEFAULT_BEAR_VOICE``
- ``HOST_VOICE_ES``, ``BULL_VOICE_ES``, ``BEAR_VOICE_ES``
- ``EMBEDDING_MODEL``, ``OPENAI_API_KEY``
"""

from __future__ import annotations

import os

_SECRET_KEYS = (
    "ANTHROPIC_API_KEY",
    "ELEVENLABS_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SONNET_MODEL",
    "OPUS_MODEL",
    "ELEVENLABS_MODEL",
    "DEFAULT_HOST_VOICE",
    "DEFAULT_BULL_VOICE",
    "DEFAULT_BEAR_VOICE",
    "HOST_VOICE_ES",
    "BULL_VOICE_ES",
    "BEAR_VOICE_ES",
    "EMBEDDING_MODEL",
    "OPENAI_API_KEY",
)


def push_secrets_to_env() -> list[str]:
    """Copy known keys from ``st.secrets`` into ``os.environ``.

    Returns the list of keys successfully pushed (useful for diagnostics).
    Safe to call multiple times; values already in ``os.environ`` are
    never overwritten.
    """
    try:
        import streamlit as st
    except ImportError:
        return []

    pushed: list[str] = []
    try:
        secrets = st.secrets
    except Exception:
        # No secrets file configured. That's fine — fall back to .env / env.
        return pushed

    for key in _SECRET_KEYS:
        if os.environ.get(key):
            continue
        try:
            value = secrets[key]  # type: ignore[index]
        except (KeyError, FileNotFoundError, Exception):
            continue
        if value is None:
            continue
        os.environ[key] = str(value)
        pushed.append(key)
    return pushed
