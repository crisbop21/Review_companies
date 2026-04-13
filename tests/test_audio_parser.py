"""Unit tests for the script parser (Step 6)."""

from __future__ import annotations

from pipeline.step6_audio import parse_script


SAMPLE = """## Act 1: Cold Open

HOST: Welcome to the show. Today we're looking at Microsoft.
BULL: Azure grew 34% year over year.
HOST: What does that mean?
BULL: It means cloud demand is still accelerating.

## Act 2: Business 101

BEAR: Every infrastructure cycle looks like this at its peak.
HOST: What do you mean "at its peak"?
BEAR: Let me walk you through a parallel from 2000.
"""


def test_parse_script_produces_segments() -> None:
    segments = parse_script(SAMPLE)
    speakers = [s.speaker for s in segments]
    assert speakers == ["HOST", "BULL", "HOST", "BULL", "BEAR", "HOST", "BEAR"]


def test_act_boundary_flags() -> None:
    segments = parse_script(SAMPLE)
    # First segment of Act 1 and first segment of Act 2 are act boundaries.
    act_boundary_indices = [i for i, s in enumerate(segments) if s.is_act_boundary]
    assert act_boundary_indices == [0, 4]


def test_multiline_speaker_text() -> None:
    script = """HOST: First line.
This is a continuation of the host's turn.
BULL: And now the bull speaks.
"""
    segments = parse_script(script)
    assert segments[0].speaker == "HOST"
    assert "continuation" in segments[0].text
    assert segments[1].speaker == "BULL"
