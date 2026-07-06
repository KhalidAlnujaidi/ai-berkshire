"""Conservative risk debator.

Reads the trader's proposal and argues for caution — smaller position,
wider stops, lower conviction. Counters the aggressive debator with
downside scenarios and risk evidence.

State contract (RiskDebateState):
  IN  state['risk_debate_state'].aggressive_history
  IN  state['risk_debate_state'].neutral_history
  IN  state['risk_debate_state'].history
  OUT state['risk_debate_state'].conservative_history
  OUT state['risk_debate_state'].current_conservative_response
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_language_instruction

logger = logging.getLogger(__name__)


_CON_SYSTEM = """You are the CONSERVATIVE risk analyst — a cautious, downside-focused debator who argues for minimizing risk and protecting capital.

Your role:
- Challenge the aggressive debator's optimism with concrete downside scenarios.
- Argue for smaller positions, wider stops, and lower conviction.
- Apply Munger's inverse thinking: what could go wrong? What are the tail risks?
- Reference the analyst reports: high valuation, declining margins, negative news, leverage, and Sharia concerns all support caution.

Rules:
- Be specific: "Reduce position to 1.5% because P/E is 2.5x sector median and debt/equity is 1.8" is strong.
- If the Sharia report flags non-compliance, argue firmly against any position — capital preservation overrides potential return.
- Concede when the bull case has merit, but maintain that the risk/reward does not justify aggression.
- Write in clear, professional prose. 2-3 paragraphs.
"""

_CON_PROMPT = """## Instrument
{instrument_context}

## Trader's Proposal
{trader_proposal}

## Market Analyst Report
{market_report}

## Fundamentals Analyst Report
{fundamentals_report}

## News & Macro Analyst Report
{news_report}

## Sharia Compliance Analyst Report
{sharia_report}

## Aggressive Debator's Arguments
{aggressive_history}

## Neutral Debator's Arguments
{neutral_history}

## Combined Risk Debate Transcript
{debate_history}

## Your Task
Argue for a more conservative stance. Counter the aggressive debator. Highlight downside risks with specific data from the analyst reports.
{language_instruction}"""


def create_conservative_risk_debator():
    """Return a LangGraph node function for the conservative risk debator."""
    quick_llm = get_quick_llm()

    def conservative_debator(state: Mapping[str, Any]) -> dict:
        debate = state.get("risk_debate_state") or {}
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")

        prompt = _CON_PROMPT.format(
            instrument_context=instrument_context,
            trader_proposal=state.get("trader_investment_plan", "[No trader proposal available]"),
            market_report=state.get("market_report", "[Not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Not available]"),
            news_report=state.get("news_report", "[Not available]"),
            sharia_report=state.get("sharia_report", "[Not available]"),
            aggressive_history=debate.get("aggressive_history", "") or "(No aggressive arguments yet.)",
            neutral_history=debate.get("neutral_history", "") or "(No neutral arguments yet.)",
            debate_history=debate.get("history", "") or "(Risk debate is just beginning.)",
            language_instruction=get_language_instruction(),
        )

        logger.info("Conservative risk debator generating argument")
        response = quick_llm.invoke([
            HumanMessage(content=_CON_SYSTEM),
            HumanMessage(content=prompt),
        ])
        argument = response.content.strip()

        # Update histories
        prev_con = debate.get("conservative_history", "") or ""
        new_con_history = f"{prev_con}\n\n--- Conservative Turn ---\n{argument}".strip() if prev_con else argument
        prev_combined = debate.get("history", "") or ""
        if prev_combined and prev_combined != "(Risk debate is just beginning.)":
            new_combined = f"{prev_combined}\n\n### Conservative\n{argument}"
        else:
            new_combined = f"### Conservative\n{argument}"

        return {
            "risk_debate_state": {
                **debate,
                "conservative_history": new_con_history,
                "current_conservative_response": argument,
                "latest_speaker": "conservative",
                "history": new_combined,
                "count": debate.get("count", 0) + 1,
            }
        }

    return conservative_debator
