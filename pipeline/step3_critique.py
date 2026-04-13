"""Step 3: Bearish critic — structured skepticism with web search."""

from __future__ import annotations

import json

from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt, load_prompt


def run(
    step1_output: dict,
    client: AnthropicClient | None = None,
) -> tuple[dict, Prompt]:
    client = client or AnthropicClient()
    prompt = load_prompt("step3_bearish_critic")

    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=(
            "Claims and concepts from Step 1 follow. Apply the five lenses.\n\n"
            f"{json.dumps(step1_output, indent=2)}"
        ),
        max_tokens=8_000,
        web_search=prompt.web_search,
    )
    return result.as_json(), prompt
