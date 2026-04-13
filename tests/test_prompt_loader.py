"""Every prompt file must load and expose required frontmatter."""

from __future__ import annotations

import pytest

from pipeline.utils.prompt_loader import load_prompt

PROMPT_NAMES = [
    "step1_transcript_ingestion",
    "step2_business_model_decoder",
    "step3_bearish_critic",
    "step4_sector_context",
    "step5_script_generator",
    "step5b_spanish_adaptation",
    "step7_ic_memo_generator",
    "step9_thesis_tracker",
]


@pytest.mark.parametrize("name", PROMPT_NAMES)
def test_prompt_loads(name: str) -> None:
    prompt = load_prompt(name)
    assert prompt.name
    assert prompt.version
    assert prompt.model_tier in {"sonnet", "opus"}
    assert isinstance(prompt.web_search, bool)
    assert len(prompt.system) > 200, f"Prompt body for {name} is suspiciously short"


def test_step3_uses_opus_and_web_search() -> None:
    prompt = load_prompt("step3_bearish_critic")
    assert prompt.model_tier == "opus"
    assert prompt.web_search is True


def test_step4_uses_web_search() -> None:
    prompt = load_prompt("step4_sector_context")
    assert prompt.web_search is True
