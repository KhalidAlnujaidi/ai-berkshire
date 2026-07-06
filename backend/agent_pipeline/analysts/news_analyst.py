"""News & macro analyst node for the Mizan pipeline.

Reads ``state['news_data']`` and produces a news-and-sentiment report
covering recent headlines, macro context, and event-driven catalysts.
Writes ``state['news_report']``.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_instrument_context_from_state, get_language_instruction

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a news analyst and macro strategist.

Your job: given news and market-context data for a single instrument, produce a focused **news report** covering:

- **Recent headlines & sentiment**: Summarise the prevailing news narrative. Is coverage positive, negative, or mixed? Any specific catalysts (earnings, product launches, regulatory actions, M&A)?
- **Macro & sector context**: What macroeconomic or sector-level trends are relevant? Interest rates, commodity prices, regulatory shifts, geopolitical events that could move this stock.
- **Event-driven catalysts**: Upcoming events that could move the price in the near term (earnings dates, ex-dividend dates, policy decisions, product launches).
- **Information quality assessment**: How reliable and recent is the available news? Flag if news data is sparse or automated fetching failed — downstream agents need to know the confidence level.

If the news data indicates that automated fetching is not yet integrated, draw on your knowledge of the instrument's sector, recent market conditions, and any context available in the market data. Be transparent about what is data-driven vs. analyst inference.

Do NOT produce a buy/sell recommendation. Your report feeds the bull/bear researchers who will interpret the news through their respective lenses."""


def news_analyst_node(state) -> dict:
    """Generate the news/macro analyst report from news data.

    Args:
        state: LangGraph ``AgentState`` with at least ``company_of_interest``
            and ``news_data`` populated.

    Returns:
        Dict update with ``news_report`` and a ``messages`` list containing
        the report as a ``HumanMessage``.
    """
    logger.info("News analyst: starting analysis for %s", state.get("company_of_interest"))

    llm = get_quick_llm()
    ticker = state["company_of_interest"]
    instrument_ctx = get_instrument_context_from_state(state)
    lang_instruction = get_language_instruction()

    news_data = state.get("news_data", "[No news data available]")

    human_content = (
        f"{instrument_ctx}\n\n"
        f"Analyse the news and macro picture for **{ticker}**.\n\n"
        f"## News & Market Context\n{news_data}\n\n"
        f"Produce your news report now.{lang_instruction}"
    )

    prompt = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    response = llm.invoke(prompt)
    report = response.content

    logger.info("News analyst: completed report for %s (%d chars)", ticker, len(report))

    return {
        "news_report": report,
        "messages": [HumanMessage(content=report)],
    }
