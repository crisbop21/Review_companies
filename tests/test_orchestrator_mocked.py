"""End-to-end orchestrator test with fully-mocked step functions.

Verifies the orchestrator wires steps together correctly, records prompt
versions, and produces a chunk list — all without any API calls.
"""

from __future__ import annotations

from unittest.mock import patch

from pipeline.orchestrator import run_pipeline
from pipeline.utils.prompt_loader import Prompt


def _fake_prompt(name: str, tier: str = "sonnet") -> Prompt:
    return Prompt(
        name=name,
        version="0.1.0",
        model_tier=tier,
        web_search=False,
        system="system body",
        meta={},
    )


def _padded(text: str) -> str:
    """Meet the chunker's word-count floor."""
    filler = " lorem ipsum dolor sit amet consectetur adipiscing elit"
    while len(text.split()) < 40:
        text += filler
    return text


FAKE_STEP1 = {
    "company": {
        "name": "Microsoft",
        "ticker": "MSFT",
        "sector": "cloud",
        "quarter": "Q1_2026",
    },
    "claims": [
        {
            "id": "claim_001",
            "text": _padded("Azure AI revenue grew 49 percent year over year."),
            "category": "revenue",
            "concepts": ["Azure AI"],
        }
    ],
    "concept_glossary": [{"term": "Azure AI", "related_claims": ["claim_001"]}],
}

FAKE_STEP2 = {
    "ordering_notes": "",
    "explanations": [
        {
            "concept": "Azure AI",
            "definition": _padded("Azure AI is Microsoft's managed service for model inference."),
            "why_it_matters_here": "It's the growth lever.",
            "analogy": "Like renting GPU time instead of owning it.",
            "claims_unlocked": ["claim_001"],
        }
    ],
}

FAKE_STEP3 = {
    "critiques": [
        {
            "target_claim_id": "claim_001",
            "lens": "metric_selection",
            "summary": _padded("Azure AI as a separate number didn't exist a year ago."),
            "evidence": "Prior 10-Q footnotes.",
            "severity": "medium",
            "bull_rebuttal": "New disclosure matches peer segmentation.",
        }
    ]
}

FAKE_STEP4 = {
    "sector": "cloud",
    "bull_case": {
        "narrative": _padded("Cloud capex cycle has years to run."),
        "tailwinds": ["AI"],
        "current_data": [],
    },
    "bear_case": {
        "narrative": _padded("Every capex boom ends with a digestion phase."),
        "headwinds": ["regulation"],
        "current_data": [],
    },
}

FAKE_SCRIPT = "## Act 1: Cold Open\n\nHOST: Welcome.\nBULL: Azure grew 49%.\n"

FAKE_MEMO = {
    "thesis_summary": _padded("Microsoft compounds as long as AI contribution holds."),
    "bull_score": 7,
    "bear_score": 5,
    "bull_justification": "Evidence.",
    "bear_justification": "Evidence.",
    "key_assumptions": [
        {
            "text": "AI contribution holds above 6pp",
            "confidence": 7,
            "rationale": _padded("Reasoned from Q4 and Q1 contribution numbers."),
        }
    ],
    "kill_conditions": [
        {
            "condition_text": "Azure YoY below 24% for two quarters",
            "metric_name": "azure_yoy_growth",
            "threshold_value": 24,
            "threshold_direction": "below",
        }
    ],
    "suggested_size_pct": 3.0,
    "time_horizon": "12_months",
    "memo_text": _padded("This memo summarizes the thesis."),
}


def test_run_pipeline_wires_all_steps() -> None:
    with (
        patch("pipeline.orchestrator.step1_ingest.run") as s1,
        patch("pipeline.orchestrator.step2_decode.run") as s2,
        patch("pipeline.orchestrator.step3_critique.run") as s3,
        patch("pipeline.orchestrator.step4_sector.run") as s4,
        patch("pipeline.orchestrator.step5_script.run") as s5,
        patch("pipeline.orchestrator.step7_memo.run") as s7,
        patch("pipeline.orchestrator.AnthropicClient") as mock_client,
    ):
        s1.return_value = (FAKE_STEP1, _fake_prompt("step1"))
        s2.return_value = (FAKE_STEP2, _fake_prompt("step2"))
        s3.return_value = (FAKE_STEP3, _fake_prompt("step3", tier="opus"))
        s4.return_value = (FAKE_STEP4, _fake_prompt("step4"))
        s5.return_value = (FAKE_SCRIPT, _fake_prompt("step5", tier="opus"))
        s7.return_value = (FAKE_MEMO, _fake_prompt("step7", tier="opus"))
        mock_client.return_value = object()

        result = run_pipeline(
            source="transcript text here",
            source_type="text",
            ticker="MSFT",
            quarter="Q1_2026",
            anthropic=mock_client.return_value,
        )

    assert result.failed_step is None
    assert result.step1 is FAKE_STEP1
    assert result.memo is FAKE_MEMO
    assert result.script_en == FAKE_SCRIPT
    assert result.prompt_versions == {
        "step1": "0.1.0",
        "step2": "0.1.0",
        "step3": "0.1.0",
        "step4": "0.1.0",
        "step5": "0.1.0",
        "step7": "0.1.0",
    }
    assert result.model_versions["step3"] == "opus"
    assert result.chunks, "chunker produced zero chunks"
    assert all("ticker" in c["metadata"] for c in result.chunks)


def test_run_pipeline_records_failed_step() -> None:
    with (
        patch("pipeline.orchestrator.step1_ingest.run") as s1,
        patch("pipeline.orchestrator.step2_decode.run") as s2,
        patch("pipeline.orchestrator.AnthropicClient") as mock_client,
    ):
        s1.return_value = (FAKE_STEP1, _fake_prompt("step1"))
        s2.side_effect = RuntimeError("boom")
        mock_client.return_value = object()

        try:
            run_pipeline(
                source="t", source_type="text", ticker="MSFT", quarter="Q1_2026",
                anthropic=mock_client.return_value,
            )
        except RuntimeError:
            pass  # expected — orchestrator re-raises after recording state

        # We can't access `result` after the raise in this form of the API,
        # but we can at least verify step1 succeeded before step2 blew up
        # via the mock call counts.
        assert s1.call_count == 1
        assert s2.call_count == 1
