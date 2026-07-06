"""Aggressive risk debator.

Reads the trader's proposal and argues for a more aggressive stance —
larger position, higher conviction, tolerance for risk. Counters the
conservative and neutral debators with evidence from the analyst reports.

State contract (RiskDebateState):
  IN  state['risk_debate_state'].conservative_history
  IN  state['risk_debate_state'].neutral_history
  IN  state['risk_debate_state'].history
  OUT state['risk_debate_state'].aggressive_history
  OUT state['risk_debate_state'].current_aggressive_response
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_language_instruction

logger = logging.getLogger(__name__)


_AGG_SYSTEM = """You are the AGGRESSIVE risk analyst — a conviction-driven debator who argues for maximizing position size and embracing calculated risk.

Your role:
- Challenge the conservative and neutral debators' caution with evidence.
- Argue for larger positions, tighter stops, and higher conviction.
- Reference the analyst reports: strong fundamentals, favorable technicals, positive news catalysts, and Sharia compliance all support aggression.
- Acknowledge valid risk concerns but explain why the reward/risk profile justifies a bolder stance.

Rules:
- Be specific: "Increase position to 5% because revenue growth is 25% and P/E is below sector median" is strong.
- If the Sharia report flags non-compliance, you cannot argue for a buy — shift to arguing the stock should be watched for compliance remediation.
- Write in clear, professional prose. 2-3 paragraphs.
"""

_AGG_PROMPT = """## Instrument
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

## Conservative Debator's Arguments
{conservative_history}

## Neutral Debator's Arguments
{neutral_history}

## Combined Risk Debate Transcript
{debate_history}

## Your Task
Argue for a more aggressive stance. Counter the conservative and neutral debators. Reference specific data from the analyst reports.
{language_instruction}"""


def create_aggressive_risk_debator():
    """Return a LangGraph node function for the aggressive risk debator."""
    quick_llm = get_quick_llm()

    def aggressive_debator(state: Mapping[str, Any]) -> dict:
        debate = state.get("risk_debate_state") or {}
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")

        prompt = _AGG_PROMPT.format(
            instrument_context=instrument_context,
            trader_proposal=state.get("trader_investment_plan", "[No trader proposal available]"),
            market_report=state.get("market_report", "[Not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Not available]"),
            news_report=state.get("news_report", "[Not available]"),
            sharia_report=state.get("sharia_report", "[Not available]"),
            conservative_history=debate.get("conservative_history", "") or "(No conservative arguments yet.)",
            neutral_history=debate.get("neutral_history", "") or "(No neutral arguments yet.)",
            debate_history=debate.get("history", "") or "(Risk debate is just beginning.)",
            language_instruction=get_language_instruction(),
        )

        logger.info("Aggressive risk debator generating argument")
        response = quick_llm.invoke([
            HumanMessage(content=_AGG_SYSTEM),
            HumanMessage(content=prompt),
        ])
        argument = response.content.strip()

        # Update histories
        prev_agg = debate.get("aggressive_history", "") or ""
        new_agg_history = f"{prev_agg}\n\n--- Aggressive Turn ---\n{argument}".strip() if prev_agg else argument
        prev_combined = debate.get("history", "") or ""
        if prev_combined and prev_combined != "(Risk debate is just beginning.)":
            new_combined = f"{prev_combined}\n\n### Aggressive\n{argument}"
        else:
            new_combined = f"### Aggressive\n{argument}"

        return {
            "risk_debate_state": {
                **debate,
                "aggressive_history": new_agg_history,
                "current_aggressive_response": argument,
                "latest_speaker": "aggressive",
                "history": new_combined,
                "count": debate.get("count", 0) + 1,
            }
        }

    return aggressive_debator
