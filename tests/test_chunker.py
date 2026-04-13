"""Unit tests for the chunker. No API calls — pure data transforms."""

from __future__ import annotations

import pytest

from pipeline.utils import chunker


def _padded(text: str, words: int = 40) -> str:
    """Pad a string so it clears the chunker's word-count floor."""
    filler = " lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod"
    while len(text.split()) < words:
        text += filler
    return text


def test_build_metadata_requires_valid_type() -> None:
    with pytest.raises(ValueError):
        chunker.build_metadata("MSFT", "Q1_2026", "not_a_real_type")


def test_build_metadata_includes_extras() -> None:
    md = chunker.build_metadata(
        "MSFT", "Q1_2026", "claim", claim_id="claim_001", category="revenue"
    )
    assert md["ticker"] == "MSFT"
    assert md["quarter"] == "Q1_2026"
    assert md["chunk_type"] == "claim"
    assert md["claim_id"] == "claim_001"
    assert md["category"] == "revenue"


def test_chunk_claims_skips_short_text() -> None:
    step1 = {
        "claims": [
            {"id": "claim_001", "text": "short", "category": "revenue"},
            {
                "id": "claim_002",
                "text": _padded("Azure revenue grew 34 percent year over year."),
                "category": "revenue",
            },
        ]
    }
    chunks = chunker.chunk_claims(step1, "MSFT", "Q1_2026")
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["claim_id"] == "claim_002"


def test_chunk_memo_always_emits_kill_conditions() -> None:
    memo = {
        "thesis_summary": _padded("Microsoft is a quality compounder."),
        "bull_score": 7,
        "bear_score": 5,
        "key_assumptions": [],
        "kill_conditions": [
            {
                "condition_text": "Azure YoY below 24%",
                "metric_name": "azure_yoy_growth",
                "threshold_value": 24,
                "threshold_direction": "below",
            }
        ],
    }
    chunks = chunker.chunk_memo(memo, "MSFT", "Q1_2026")
    types = [c["chunk_type"] for c in chunks]
    assert "thesis_summary" in types
    assert "kill_condition" in types


def test_chunk_all_is_deterministic() -> None:
    step1 = {
        "claims": [
            {
                "id": "claim_001",
                "text": _padded("Azure AI grew 49 percent year over year."),
                "category": "revenue",
            }
        ],
        "concept_glossary": [],
    }
    first = chunker.chunk_all(ticker="MSFT", quarter="Q1_2026", step1=step1)
    second = chunker.chunk_all(ticker="MSFT", quarter="Q1_2026", step1=step1)
    assert first == second


def test_max_word_trimming() -> None:
    long_text = "word " * 400
    step1 = {
        "claims": [
            {"id": "claim_001", "text": long_text, "category": "revenue"}
        ]
    }
    chunks = chunker.chunk_claims(step1, "MSFT", "Q1_2026")
    assert len(chunks) == 1
    assert len(chunks[0]["chunk_text"].split()) <= chunker._MAX_WORDS
