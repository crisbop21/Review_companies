"""Step 4: Sector context — bull and bear narratives with current data."""

from __future__ import annotations

from pipeline.utils.anthropic_client import AnthropicClient
from pipeline.utils.prompt_loader import Prompt, load_prompt


def run(
    transcript: str,
    client: AnthropicClient | None = None,
) -> tuple[dict, Prompt]:
    client = client or AnthropicClient()
    prompt = load_prompt("step4_sector_context")

    result = client.complete(
        tier=prompt.model_tier,  # type: ignore[arg-type]
        system=prompt.system,
        user=f"Transcript:\n\n{transcript}",
        max_tokens=6_000,
        web_search=prompt.web_search,
    )
    return result.as_json(), prompt
