"""Step 7: IC memo generator — scored bull/bear, assumptions, kill conditions."""

from __future__ import annotations

import json

from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt, load_prompt


def run(
    pipeline_outputs: dict,
    client: AnthropicClient | None = None,
) -> tuple[dict, Prompt]:
    """Produce the IC memo JSON.

    Args:
        pipeline_outputs: dict with keys ``claims_concepts``, ``explanations``,
            ``critiques``, ``sector``, ``script``. Script may be omitted if
            the memo is generated before the script.
    """
    client = client or AnthropicClient()
    prompt = load_prompt("step7_ic_memo_generator")

    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=(
            "Upstream pipeline outputs follow. Produce the IC memo per the "
            "system instructions. Be strict with scoring calibration.\n\n"
            f"{json.dumps(pipeline_outputs, indent=2)}"
        ),
        max_tokens=6_000,
        web_search=prompt.web_search,
    )
    return result.as_json(), prompt
