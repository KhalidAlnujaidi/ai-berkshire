"""LLM factory helpers for the Mizan agent pipeline.

Centralises ChatOpenAI construction so every node uses identical provider
settings (OpenRouter, OpenAI-compatible).  Two tiers are exposed:

- ``get_deep_llm`` — lower temperature, used by the Research Manager and
  Portfolio Manager where the final judgement is rendered.
- ``get_quick_llm`` — higher temperature, used by analysts, researchers,
  debaters, and the trader for diverse, exploratory analysis.

Both factories are cheap to call; they construct a fresh ``ChatOpenAI``
instance each time so structured-output bindings on one instance never leak
into another node.
"""

from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI

from agent_pipeline import config

logger = logging.getLogger(__name__)


def get_deep_llm() -> ChatOpenAI:
    """Return a ``ChatOpenAI`` configured for deep, deliberate reasoning.

    Used by the Research Manager and Portfolio Manager — the two nodes
    that produce the final, structured investment decision.
    """
    return ChatOpenAI(
        model=config.DEEP_THINK_LLM,
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
        max_tokens=config.MAX_TOKENS,
        temperature=0.3,
    )


def get_quick_llm() -> ChatOpenAI:
    """Return a ``ChatOpenAI`` configured for fast, exploratory analysis.

    Used by the four analysts (market, fundamentals, news, sharia), the
    bull/bear researchers, the risk debaters, and the trader.  The higher
    temperature encourages independent perspectives across agents.
    """
    return ChatOpenAI(
        model=config.QUICK_THINK_LLM,
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
        max_tokens=config.MAX_TOKENS,
        temperature=0.7,
    )
