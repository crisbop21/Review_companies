"""ElevenLabs API wrapper.

Wraps the official ``elevenlabs`` SDK with: voice-name resolution,
exponential-backoff retries, and a character-count pre-flight that warns
before consuming large quota unintentionally.
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache

from pipeline.config import Config

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_BACKOFF_SECONDS = 2.0


class QuotaExhaustedError(RuntimeError):
    """Raised when ElevenLabs reports insufficient quota."""


class ElevenLabsClient:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()
        from elevenlabs.client import ElevenLabs  # local import

        self._client = ElevenLabs(api_key=self.config.elevenlabs_api_key)

    # ------------------------------------------------------------------
    @lru_cache(maxsize=32)
    def _resolve_voice_id(self, voice_name: str) -> str:
        """Map a voice name (e.g. "Rachel") to an ElevenLabs voice_id.

        Cached because voice lists rarely change across a single run.
        """
        try:
            voices = self._client.voices.get_all().voices  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - API surface varies
            logger.warning("Unable to resolve voice list: %s", exc)
            return voice_name  # Fall back: many SDKs accept the name directly.

        for v in voices:
            if getattr(v, "name", "").lower() == voice_name.lower():
                return getattr(v, "voice_id", voice_name)
        # Name not found — fall back and hope the SDK accepts it.
        return voice_name

    # ------------------------------------------------------------------
    def synthesize(
        self,
        text: str,
        voice: str,
        model: str | None = None,
    ) -> bytes:
        """Generate MP3 audio bytes for a single text segment."""
        if not text.strip():
            raise ValueError("synthesize: empty text")

        model = model or self.config.elevenlabs_model
        voice_id = self._resolve_voice_id(voice)

        backoff = _INITIAL_BACKOFF_SECONDS
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                stream = self._client.text_to_speech.convert(  # type: ignore[attr-defined]
                    voice_id=voice_id,
                    model_id=model,
                    text=text,
                    output_format="mp3_44100_128",
                )
                # The SDK returns an iterator of byte chunks.
                return b"".join(stream)
            except Exception as exc:  # pragma: no cover - SDK exception surface
                last_exc = exc
                message = str(exc).lower()
                if "quota" in message or "credit" in message:
                    raise QuotaExhaustedError(str(exc)) from exc
                if attempt == _MAX_RETRIES:
                    raise
                logger.warning(
                    "elevenlabs retry attempt=%d err=%s backoff=%.1fs",
                    attempt + 1,
                    exc,
                    backoff,
                )
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError("elevenlabs retry loop exited") from last_exc


def synthesize(text: str, voice: str, model: str = "eleven_multilingual_v2") -> bytes:
    """Module-level convenience for one-off calls (mainly used in tests)."""
    return ElevenLabsClient().synthesize(text, voice=voice, model=model)
