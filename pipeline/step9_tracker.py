"""Step 9: Thesis tracker — delta report on repeat runs."""

from __future__ import annotations

import json

from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt, load_prompt


def run(
    current_outputs: dict,
    prior_memo: dict,
    prior_outputs: dict,
    client: AnthropicClient | None = None,
) -> tuple[dict, Prompt]:
    """Compare current-quarter analysis to the prior IC memo.

    Args:
        current_outputs: all Step 1–5 outputs for the current run.
        prior_memo: the IC memo JSON from the previous quarter.
        prior_outputs: the previous quarter's Step 1–5 outputs, for context.
    """
    client = client or AnthropicClient()
    prompt = load_prompt("step9_thesis_tracker")

    bundle = {
        "current_quarter": current_outputs,
        "prior_quarter_memo": prior_memo,
        "prior_quarter_outputs": prior_outputs,
    }
    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=(
            "Prior-memo and current-quarter outputs follow. Produce the "
            "delta report per the system instructions.\n\n"
            f"{json.dumps(bundle, indent=2)}"
        ),
        max_tokens=6_000,
        web_search=prompt.web_search,
    )
    return result.as_json(), prompt
