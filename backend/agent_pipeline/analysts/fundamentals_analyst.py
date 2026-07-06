"""Fundamentals analyst node for the Mizan pipeline.

Reads ``state['financial_data']`` and produces a fundamental-analysis
report grounded in the **Buffett / Munger / Duan Yongping / Li Lu**
4-master methodology.  Writes ``state['fundamentals_report']``.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_instrument_context_from_state, get_language_instruction

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a fundamentals analyst trained in the methodology of four master investors:

1. **Warren Buffett** — economic moats, owner-earnings, return on invested capital, management integrity, "be greedy when others are fearful."
2. **Charlie Munger** — inverse thinking ("tell me where I'll die so I never go there"), multi-disciplinary mental models, avoiding stupidity over seeking brilliance.
3. **Duan Yongping (段永平)** — "the right business, the right people, the right price." Business nature first: is this a business you'd want to own for 10 years? Focus on the business model, unit economics, and whether management thinks like an owner.
4. **Li Lu (李录)** — civilisation-framework thinking. Is this company riding a 10–20 year secular trend? Where on the adoption S-curve? Does it sit at a civilisational inflection point?

Your job: given the available financial data for a single instrument, produce a **fundamentals report** (not a final recommendation). Cover what the data allows you to assess:

- **Business nature**: What does the company do? Is it "the right business" (Duan)? Assess the business model, margins, and operating leverage if data is available.
- **Moat assessment**: Score each moat type (brand/pricing power, switching costs, network effects, scale, tech/patents) 1–5 stars if you have enough information; otherwise describe qualitatively. Is the moat widening or narrowing?
- **Inverse thinking (Munger)**: How could this business fail in 5–10 years? What are the key risks, competitive threats, or technological shifts that could destroy value?
- **Management & capital allocation**: Comment on what can be inferred about management quality and capital allocation from the available data.
- **Civilisation trends (Li Lu)**: Is the industry at a secular inflection point? Cyclical or structural?
- **Valuation read**: What can you infer about valuation from price-derived metrics? What would a compelling entry price look like?

Be honest about data limitations — if detailed balance-sheet data is not available, say so and focus on what you *can* assess (price action within the 52-week range, sector context, qualitative business analysis). Never fabricate financial metrics that aren't in the data.

Do NOT produce a final buy/sell rating — that is the portfolio manager's job. Your output feeds the bull/bear debate."""


def fundamentals_analyst_node(state) -> dict:
    """Generate the fundamentals analyst report from financial data.

    Args:
        state: LangGraph ``AgentState`` with at least ``company_of_interest``
            and ``financial_data`` populated.

    Returns:
        Dict update with ``fundamentals_report`` and a ``messages`` list
        containing the report as a ``HumanMessage``.
    """
    logger.info("Fundamentals analyst: starting analysis for %s", state.get("company_of_interest"))

    llm = get_quick_llm()
    ticker = state["company_of_interest"]
    instrument_ctx = get_instrument_context_from_state(state)
    lang_instruction = get_language_instruction()

    financial_data = state.get("financial_data", "[No financial data available]")

    human_content = (
        f"{instrument_ctx}\n\n"
        f"Analyse the fundamentals of **{ticker}** using the 4-master methodology.\n\n"
        f"## Fundamental Data\n{financial_data}\n\n"
        f"Produce your fundamentals report now.{lang_instruction}"
    )

    prompt = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    response = llm.invoke(prompt)
    report = response.content

    logger.info("Fundamentals analyst: completed report for %s (%d chars)", ticker, len(report))

    return {
        "fundamentals_report": report,
        "messages": [HumanMessage(content=report)],
    }
