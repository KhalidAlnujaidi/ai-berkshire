"""Trader.

Reads the Research Manager's investment plan and all analyst reports,
then uses the **deep LLM** with structured output (``TraderProposal``)
to produce ``state['trader_investment_plan']`` — a concrete transaction
proposal (Buy / Hold / Sell) with entry price, stop loss, and position
sizing guidance.

The trader sits between the investment debate and the risk debate. It
translates the Research Manager's recommendation into an actionable
trade, which the risk debators then challenge.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage

from agent_pipeline.llm import get_deep_llm
from agent_pipeline.schemas import TraderProposal, render_trader_proposal
from agent_pipeline.structured import bind_structured, invoke_structured_or_freetext
from agent_pipeline.utils import get_language_instruction

logger = logging.getLogger(__name__)


_TRADER_SYSTEM = """You are the Trader — a pragmatic execution specialist who translates the Research Manager's investment plan into a concrete transaction proposal.

Your role:
1. Read the investment plan (recommendation + strategic actions).
2. Cross-reference the analyst reports for entry/exit levels.
3. Issue a transaction proposal: Buy, Hold, or Sell.
4. Specify entry price, stop-loss, and position sizing when applicable.

Rules:
- If the investment plan is "Non-Compliant", your action MUST be "Hold" (do not buy) and you should note that Sharia non-compliance prevents entry.
- If the plan is "Avoid" or "Watch", your action should be "Hold" (no position).
- If the plan is "Strong Buy" or "Buy", propose a "Buy" with specific entry/stop levels.
- Position sizing should be conservative: typically 2-5% of portfolio for a Buy, less for speculative positions.
- Entry price and stop-loss should be anchored to the market data in the reports, not invented.
"""

_TRADER_PROMPT = """## Instrument
{instrument_context}

## Investment Plan (from Research Manager)
{investment_plan}

## Market Analyst Report (for price levels)
{market_report}

## Fundamentals Analyst Report (for valuation context)
{fundamentals_report}

## Sharia Compliance Report
{sharia_report}

## Your Task
Translate the investment plan into a concrete transaction proposal. Specify action, reasoning, entry price, stop loss, and position sizing.
{language_instruction}"""


def create_trader():
    """Return a LangGraph node function for the Trader."""
    deep_llm = get_deep_llm()
    structured_llm = bind_structured(deep_llm, TraderProposal, "trader")

    def trader(state: Mapping[str, Any]) -> dict:
        investment_plan = state.get("investment_plan", "") or "[No investment plan available]"
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")

        prompt = _TRADER_PROMPT.format(
            instrument_context=instrument_context,
            investment_plan=investment_plan,
            market_report=state.get("market_report", "[Market report not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Fundamentals report not available]"),
            sharia_report=state.get("sharia_report", "[Sharia report not available]"),
            language_instruction=get_language_instruction(),
        )

        logger.info("Trader generating transaction proposal")
        trader_investment_plan = invoke_structured_or_freetext(
            structured_llm,
            deep_llm,
            [HumanMessage(content=_TRADER_SYSTEM), HumanMessage(content=prompt)],
            render_trader_proposal,
            "trader",
        )

        return {
            "trader_investment_plan": trader_investment_plan,
        }

    return trader
