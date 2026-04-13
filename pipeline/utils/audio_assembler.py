"""Concatenate ElevenLabs MP3 segments into a single episode file.

Gap rules (per IMPLEMENTATION_PLAN Task 2.2):

- 300 ms silence between turns within an act
- 800 ms silence between acts (first segment of the new act)

The first segment gets no leading silence.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

TURN_GAP_MS = 300
ACT_GAP_MS = 800


def assemble(
    segments: list[tuple[bytes, bool]],
    output_path: str,
) -> str:
    """Concatenate MP3 byte blobs and write ``output_path``.

    Args:
        segments: list of ``(mp3_bytes, is_act_boundary)`` tuples in order.
        output_path: where to write the final MP3.

    Returns:
        ``output_path``.
    """
    from pydub import AudioSegment

    if not segments:
        raise ValueError("No segments to assemble.")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    combined = AudioSegment.silent(duration=0)
    for i, (audio_bytes, is_act_boundary) in enumerate(segments):
        clip = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        if i == 0:
            combined += clip
            continue
        gap_ms = ACT_GAP_MS if is_act_boundary else TURN_GAP_MS
        combined += AudioSegment.silent(duration=gap_ms) + clip

    combined.export(str(out_path), format="mp3")
    logger.info("audio assembled: %s (%.1fs)", out_path, len(combined) / 1000.0)
    return str(out_path)
