"""Step 5: Script generator — 6,500–7,500 word three-voice script.

Step 5b (Spanish adaptation) also lives here since it is a variant of the
same task that consumes the English output rather than the upstream JSON.
"""

from __future__ import annotations

import json

from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt, load_prompt


def run(
    step1_output: dict,
    step2_output: dict,
    step3_output: dict,
    step4_output: dict,
    client: AnthropicClient | None = None,
) -> tuple[str, Prompt]:
    """Generate the English script."""
    client = client or AnthropicClient()
    prompt = load_prompt("step5_script_generator")

    bundle = {
        "claims_concepts": step1_output,
        "explanations": step2_output,
        "critiques": step3_output,
        "sector": step4_output,
    }
    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=(
            "All upstream outputs follow. Produce the seven-act script per "
            "the system instructions.\n\n"
            f"{json.dumps(bundle, indent=2)}"
        ),
        max_tokens=16_000,
        web_search=prompt.web_search,
    )
    return result.text.strip(), prompt


def adapt_spanish(
    english_script: str,
    client: AnthropicClient | None = None,
) -> tuple[str, Prompt]:
    """Adapt the English script to Latin American Spanish (Step 5b)."""
    client = client or AnthropicClient()
    prompt = load_prompt("step5b_spanish_adaptation")

    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=f"English script follows.\n\n{english_script}",
        max_tokens=16_000,
        web_search=prompt.web_search,
    )
    return result.text.strip(), prompt
