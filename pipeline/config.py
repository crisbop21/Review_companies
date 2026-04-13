"""Centralized configuration loader.

All environment variables are loaded here. Callers must import from this module
rather than reading os.environ directly so that missing keys fail fast with a
clear error at startup.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


def _optional(name: str, default: str) -> str:
    return os.environ.get(name) or default


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    elevenlabs_api_key: str
    supabase_url: str
    supabase_anon_key: str

    # Model selection defaults
    sonnet_model: str = "claude-sonnet-4-6"
    opus_model: str = "claude-opus-4-6"

    # ElevenLabs defaults
    elevenlabs_model: str = "eleven_multilingual_v2"
    host_voice_en: str = "Rachel"
    bull_voice_en: str = "Antoni"
    bear_voice_en: str = "Clyde"

    # RAG (populated only when RAG is enabled)
    embedding_model: str | None = None
    openai_api_key: str | None = None

    @classmethod
    def load(cls) -> "Config":
        return cls(
            anthropic_api_key=_require("ANTHROPIC_API_KEY"),
            elevenlabs_api_key=_require("ELEVENLABS_API_KEY"),
            supabase_url=_require("SUPABASE_URL"),
            supabase_anon_key=_require("SUPABASE_ANON_KEY"),
            sonnet_model=_optional("SONNET_MODEL", "claude-sonnet-4-6"),
            opus_model=_optional("OPUS_MODEL", "claude-opus-4-6"),
            elevenlabs_model=_optional("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
            host_voice_en=_optional("DEFAULT_HOST_VOICE", "Rachel"),
            bull_voice_en=_optional("DEFAULT_BULL_VOICE", "Antoni"),
            bear_voice_en=_optional("DEFAULT_BEAR_VOICE", "Clyde"),
            embedding_model=os.environ.get("EMBEDDING_MODEL"),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
        )
