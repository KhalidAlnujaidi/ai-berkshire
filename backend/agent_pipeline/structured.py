"""Shared helpers for structured-output invocation with graceful fallback.

Ported directly from TradingAgents — the pattern is battle-tested across
multiple LLM providers. The idea:

1. At agent creation, wrap the LLM with ``with_structured_output(Schema)``.
2. At invocation, run the structured call and render the result to markdown.
3. If the structured call fails (weak model, transient error), fall back to
   a plain ``llm.invoke()`` so the pipeline never blocks.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def bind_structured(llm: Any, schema: type[T], agent_name: str) -> Any | None:
    """Return ``llm.with_structured_output(schema)`` or ``None`` if unsupported."""
    try:
        return llm.with_structured_output(schema)
    except (NotImplementedError, AttributeError) as exc:
        logger.warning(
            "%s: provider does not support with_structured_output (%s); "
            "falling back to free-text generation",
            agent_name, exc,
        )
        return None


def invoke_structured_or_freetext(
    structured_llm: Any | None,
    plain_llm: Any,
    prompt: Any,
    render: Callable[[T], str],
    agent_name: str,
) -> str:
    """Run the structured call and render to markdown; fall back to free-text."""
    if structured_llm is not None:
        try:
            result = structured_llm.invoke(prompt)
            if result is None:
                raise ValueError("structured output returned no parsed result")
            return render(result)
        except Exception as exc:
            logger.warning(
                "%s: structured-output invocation failed (%s); retrying as free text",
                agent_name, exc,
            )

    response = plain_llm.invoke(prompt)
    return response.content
