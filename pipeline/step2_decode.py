"""Step 2: Business model decoder — ordered explanations with analogies."""

from __future__ import annotations

import json

from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt, load_prompt


def run(
    step1_output: dict,
    client: AnthropicClient | None = None,
) -> tuple[dict, Prompt]:
    client = client or AnthropicClient()
    prompt = load_prompt("step2_business_model_decoder")

    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=(
            "Step 1 output follows. Produce ordered explanations per the "
            "system instructions.\n\n"
            f"{json.dumps(step1_output, indent=2)}"
        ),
        max_tokens=8_000,
        web_search=prompt.web_search,
    )
    return result.as_json(), prompt
