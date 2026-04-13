"""Step 6: Convert a script into a single MP3 via ElevenLabs + pydub."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from pipeline.config import Config
from pipeline.utils.audio_assembler import assemble
from pipeline.utils.elevenlabs_client import ElevenLabsClient

logger = logging.getLogger(__name__)

# Matches a speaker tag at the start of a line: "HOST:", "BULL:", "BEAR:"
_TAG_RE = re.compile(r"^(HOST|BULL|BEAR):\s*(.*)$")
# Matches an act header: "## Act 1: Cold Open" or "## Acto 3: El Debate"
_ACT_RE = re.compile(r"^##\s+Act[o]?\s+\d+", re.IGNORECASE)


@dataclass
class Segment:
    speaker: str  # "HOST" | "BULL" | "BEAR"
    text: str
    is_act_boundary: bool  # True if this segment starts a new act


def parse_script(script: str) -> list[Segment]:
    """Split a script into speaker segments and flag act boundaries."""
    segments: list[Segment] = []
    pending_act_boundary = False
    current_speaker: str | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal pending_act_boundary, current_speaker, current_text
        if current_speaker and current_text:
            segments.append(
                Segment(
                    speaker=current_speaker,
                    text=" ".join(current_text).strip(),
                    is_act_boundary=pending_act_boundary,
                )
            )
            pending_act_boundary = False
            current_text = []

    for line in script.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _ACT_RE.match(stripped):
            flush()
            pending_act_boundary = True
            continue
        tag_match = _TAG_RE.match(stripped)
        if tag_match:
            flush()
            current_speaker = tag_match.group(1)
            tail = tag_match.group(2).strip()
            current_text = [tail] if tail else []
        else:
            current_text.append(stripped)
    flush()
    return segments


def _voices_for_language(config: Config, language: str) -> dict[str, str]:
    if language == "en":
        return {
            "HOST": config.host_voice_en,
            "BULL": config.bull_voice_en,
            "BEAR": config.bear_voice_en,
        }
    if language == "es":
        # Spanish voices are configured in .env or fall back to the English
        # voices used with multilingual_v2 (which handles Spanish well).
        import os

        return {
            "HOST": os.environ.get("HOST_VOICE_ES", config.host_voice_en),
            "BULL": os.environ.get("BULL_VOICE_ES", config.bull_voice_en),
            "BEAR": os.environ.get("BEAR_VOICE_ES", config.bear_voice_en),
        }
    raise ValueError(f"Unsupported language: {language!r}")


def run(
    script: str,
    output_path: str,
    language: str = "en",
    client: ElevenLabsClient | None = None,
    config: Config | None = None,
) -> str:
    """Generate ``output_path`` MP3 from the script. Returns the output path."""
    config = config or Config.load()
    client = client or ElevenLabsClient(config=config)
    voices = _voices_for_language(config, language)

    segments = parse_script(script)
    if not segments:
        raise ValueError("Script parser produced zero segments.")

    audio_segments: list[tuple[bytes, bool]] = []
    for i, seg in enumerate(segments, start=1):
        voice = voices.get(seg.speaker)
        if not voice:
            raise ValueError(f"No voice configured for speaker {seg.speaker!r}.")
        logger.info("audio segment %d/%d speaker=%s", i, len(segments), seg.speaker)
        audio = client.synthesize(seg.text, voice=voice)
        audio_segments.append((audio, seg.is_act_boundary))

    assemble(audio_segments, output_path)
    return output_path
