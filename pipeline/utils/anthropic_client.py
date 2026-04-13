"""Single-point Anthropic API wrapper for the pipeline.

Responsibilities (per IMPLEMENTATION_PLAN Task 1.1):
- Route calls to Sonnet or Opus without callers knowing the model IDs.
- Enable/disable the built-in ``web_search`` tool per call.
- Retry transient failures with exponential backoff.
- Log token usage to stderr for cost tracking.
- Parse JSON responses when a schema is requested.

Every pipeline step MUST go through this module so that prompt-version and
model-version provenance can be captured uniformly in ``analysis_runs``.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Literal

import anthropic

from pipeline.config import Config

logger = logging.getLogger(__name__)

ModelTier = Literal["sonnet", "opus"]

# Transient HTTP statuses we will retry on. 429 = rate limit, 5xx = server.
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 4
_INITIAL_BACKOFF_SECONDS = 2.0


@dataclass
class CallResult:
    """Envelope returned from :meth:`AnthropicClient.complete`."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None
    raw: Any = field(repr=False, default=None)

    def as_json(self) -> Any:
        """Parse ``text`` as JSON, tolerating fenced code blocks."""
        return _extract_json(self.text)


class AnthropicClient:
    """Thin wrapper around :class:`anthropic.Anthropic`."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()
        self._client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def complete(
        self,
        *,
        tier: ModelTier,
        system: str,
        user: str,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        web_search: bool = False,
        extra_tools: list[dict] | None = None,
    ) -> CallResult:
        """Issue a single completion request.

        Args:
            tier: ``"sonnet"`` for standard steps, ``"opus"`` for reasoning-
                heavy steps like the bearish critic.
            system: System prompt. Pass the full prompt text from
                ``prompts/stepN_*.md``.
            user: User-turn content. Usually the upstream-step JSON plus a
                short instruction to produce output.
            max_tokens: Output token budget.
            temperature: Claude sampling temperature.
            web_search: When True, attach Anthropic's built-in
                ``web_search_20250305`` tool so the model can ground claims in
                current data (used by Steps 3 and 4).
            extra_tools: Additional tool definitions to expose to the model.
        """
        model = self._resolve_model(tier)
        tools = list(extra_tools or [])
        if web_search:
            tools.append({"type": "web_search_20250305", "name": "web_search"})

        kwargs: dict[str, Any] = {
            "model": model,
            "system": system,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
        }
        if tools:
            kwargs["tools"] = tools

        response = self._call_with_retry(kwargs)
        text = _concat_text_blocks(response.content)

        usage = getattr(response, "usage", None)
        in_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        out_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        logger.info(
            "anthropic.complete model=%s in=%d out=%d stop=%s",
            model,
            in_tokens,
            out_tokens,
            getattr(response, "stop_reason", None),
        )

        return CallResult(
            text=text,
            model=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            stop_reason=getattr(response, "stop_reason", None),
            raw=response,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _resolve_model(self, tier: ModelTier) -> str:
        if tier == "sonnet":
            return self.config.sonnet_model
        if tier == "opus":
            return self.config.opus_model
        raise ValueError(f"Unknown model tier: {tier!r}")

    def _call_with_retry(self, kwargs: dict[str, Any]):
        backoff = _INITIAL_BACKOFF_SECONDS
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return self._client.messages.create(**kwargs)
            except anthropic.APIStatusError as exc:
                last_exc = exc
                if exc.status_code not in _RETRYABLE_STATUSES:
                    raise
                if attempt == _MAX_RETRIES:
                    raise
                logger.warning(
                    "anthropic retry attempt=%d status=%s backoff=%.1fs",
                    attempt + 1,
                    exc.status_code,
                    backoff,
                )
            except anthropic.APIConnectionError as exc:
                last_exc = exc
                if attempt == _MAX_RETRIES:
                    raise
                logger.warning(
                    "anthropic connection error attempt=%d backoff=%.1fs",
                    attempt + 1,
                    backoff,
                )
            time.sleep(backoff)
            backoff *= 2
        # Unreachable: either returned or raised above.
        raise RuntimeError("retry loop exited without result") from last_exc


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _concat_text_blocks(content: list) -> str:
    """Join the ``text`` pieces of an Anthropic response's content array."""
    parts: list[str] = []
    for block in content or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts)


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _extract_json(text: str) -> Any:
    """Parse JSON, stripping a single ```json fence if present."""
    stripped = text.strip()
    match = _FENCE_RE.search(stripped)
    if match:
        stripped = match.group(1).strip()
    return json.loads(stripped)
