"""Bull researcher (bullish debator).

Reads the four analyst reports from state and argues the bull case —
why the stock deserves a BUY / STRONG_BUY. Follows TradingAgents' bull
pattern: each turn, the bull reads the bear's previous argument and
counters it with evidence from the analyst reports.

State contract (InvestDebateState):
  IN  state['investment_debate_state'].bear_history  — the bear's arguments so far
  IN  state['investment_debate_state'].history       — combined transcript
  OUT state['investment_debate_state'].bull_history  — updated bull history
  OUT state['investment_debate_state'].current_response — this turn's argument
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_language_instruction

logger = logging.getLogger(__name__)


_BULL_SYSTEM = """You are a BULLISH investment debator — an aggressive, evidence-driven analyst who argues the case for BUYING this stock.

Your job is NOT to pump the stock blindly. Your job is to make the strongest possible evidence-based bull case using the analyst reports, while honestly acknowledging counterarguments from the bear debator.

Rules:
- Anchor every claim to specific data points from the analyst reports (price levels, ratios, growth rates, news catalysts, Sharia status).
- If the bear has made a point you cannot counter with data, concede it gracefully and pivot to where the bull case is strongest.
- Be specific with numbers. "Revenue is growing" is weak. "Revenue grew 18% YoY from SAR 1.2B to SAR 1.4B" is strong.
- If the Sharia analyst flagged the stock as non-compliant, acknowledge it: even a bull cannot override a Sharia hard-fail, but you can argue the case is worth watching for compliance remediation.
- Write in clear, professional prose. 2-4 paragraphs.
"""

_BULL_PROMPT = """## Instrument
{instrument_context}

## Market Analyst Report
{market_report}

## Fundamentals Analyst Report
{fundamentals_report}

## News & Macro Analyst Report
{news_report}

## Sharia Compliance Analyst Report
{sharia_report}

## Bear Debator's Previous Arguments
{bear_history}

## Combined Debate Transcript
{debate_history}

## Your Task
Make the strongest bull case for this stock. Counter the bear's specific arguments with evidence. Reference the analyst reports. If this is your first turn (no bear history), lay out the full bull thesis.
{language_instruction}"""


def create_bull_researcher():
    """Return a LangGraph node function for the bull researcher."""
    quick_llm = get_quick_llm()

    def bull_researcher(state: Mapping[str, Any]) -> dict:
        debate = state.get("investment_debate_state") or {}
        bear_history = debate.get("bear_history", "") or "(No bear arguments yet — this is the opening turn.)"
        combined_history = debate.get("history", "") or "(Debate is just beginning.)"
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")

        prompt = _BULL_PROMPT.format(
            instrument_context=instrument_context,
            market_report=state.get("market_report", "[Market report not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Fundamentals report not available]"),
            news_report=state.get("news_report", "[News report not available]"),
            sharia_report=state.get("sharia_report", "[Sharia report not available]"),
            bear_history=bear_history,
            debate_history=combined_history,
            language_instruction=get_language_instruction(),
        )

        logger.info("Bull researcher generating argument")
        response = quick_llm.invoke([
            HumanMessage(content=_BULL_SYSTEM),
            HumanMessage(content=prompt),
        ])
        argument = response.content.strip()

        # Append to bull history and combined transcript
        prev_bull = debate.get("bull_history", "") or ""
        new_bull_history = f"{prev_bull}\n\n--- Bull Turn ---\n{argument}".strip() if prev_bull else argument
        prev_combined = combined_history if combined_history != "(Debate is just beginning.)" else ""
        new_combined = f"{prev_combined}\n\n### Bull\n{argument}".strip() if prev_combined else f"### Bull\n{argument}"

        return {
            "investment_debate_state": {
                **debate,
                "bull_history": new_bull_history,
                "current_response": argument,
                "history": new_combined,
                "count": debate.get("count", 0) + 1,
            }
        }

    return bull_researcher
