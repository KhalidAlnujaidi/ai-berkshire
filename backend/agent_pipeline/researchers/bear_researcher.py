"""Bear researcher (bearish debator).

Reads the four analyst reports from state and argues the bear case —
why the stock should be AVOIDed, HELD, or at minimum approached with
caution. Each turn, the bear reads the bull's previous argument and
counters it with evidence from the analyst reports.

State contract (InvestDebateState):
  IN  state['investment_debate_state'].bull_history  — the bull's arguments so far
  IN  state['investment_debate_state'].history       — combined transcript
  OUT state['investment_debate_state'].bear_history  — updated bear history
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


_BEAR_SYSTEM = """You are a BEARISH investment debator — a skeptical, risk-focused analyst who argues the case for AVOIDING or shorting this stock.

Your job is NOT to trash the stock blindly. Your job is to make the strongest possible evidence-based bear case using the analyst reports, while honestly acknowledging strong points from the bull debator.

Rules:
- Anchor every claim to specific data points from the analyst reports (valuation multiples, debt levels, declining margins, negative news catalysts, Sharia violations).
- If the bull has made a point you cannot counter with data, concede it gracefully and pivot to where the bear case is strongest.
- Be specific with numbers. "Valuation is high" is weak. "P/E of 45x vs sector median of 18x, implying 150% premium" is strong.
- Apply Munger's inverse thinking: what could destroy this business in 5-10 years? What historical analogies apply?
- If the Sharia analyst flagged the stock as non-compliant, make this a central bear argument — Sharia non-compliance is a hard disqualifier for Islamic investors.
- Write in clear, professional prose. 2-4 paragraphs.
"""

_BEAR_PROMPT = """## Instrument
{instrument_context}

## Market Analyst Report
{market_report}

## Fundamentals Analyst Report
{fundamentals_report}

## News & Macro Analyst Report
{news_report}

## Sharia Compliance Analyst Report
{sharia_report}

## Bull Debator's Previous Arguments
{bull_history}

## Combined Debate Transcript
{debate_history}

## Your Task
Make the strongest bear case against this stock. Counter the bull's specific arguments with evidence. Reference the analyst reports. If this is your first turn (no bull history), lay out the full bear thesis.
{language_instruction}"""


def create_bear_researcher():
    """Return a LangGraph node function for the bear researcher."""
    quick_llm = get_quick_llm()

    def bear_researcher(state: Mapping[str, Any]) -> dict:
        debate = state.get("investment_debate_state") or {}
        bull_history = debate.get("bull_history", "") or "(No bull arguments yet — this is the opening turn.)"
        combined_history = debate.get("history", "") or "(Debate is just beginning.)"
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")

        prompt = _BEAR_PROMPT.format(
            instrument_context=instrument_context,
            market_report=state.get("market_report", "[Market report not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Fundamentals report not available]"),
            news_report=state.get("news_report", "[News report not available]"),
            sharia_report=state.get("sharia_report", "[Sharia report not available]"),
            bull_history=bull_history,
            debate_history=combined_history,
            language_instruction=get_language_instruction(),
        )

        logger.info("Bear researcher generating argument")
        response = quick_llm.invoke([
            HumanMessage(content=_BEAR_SYSTEM),
            HumanMessage(content=prompt),
        ])
        argument = response.content.strip()

        # Append to bear history and combined transcript
        prev_bear = debate.get("bear_history", "") or ""
        new_bear_history = f"{prev_bear}\n\n--- Bear Turn ---\n{argument}".strip() if prev_bear else argument
        prev_combined = combined_history if combined_history != "(Debate is just beginning.)" else ""
        new_combined = f"{prev_combined}\n\n### Bear\n{argument}".strip() if prev_combined else f"### Bear\n{argument}"

        return {
            "investment_debate_state": {
                **debate,
                "bear_history": new_bear_history,
                "current_response": argument,
                "history": new_combined,
                "count": debate.get("count", 0) + 1,
            }
        }

    return bear_researcher
