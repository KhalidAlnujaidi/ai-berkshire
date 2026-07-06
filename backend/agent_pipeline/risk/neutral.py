"""Neutral risk debator.

Reads the trader's proposal and provides a balanced, evidence-weighted
perspective — neither aggressive nor conservative. Weighs both sides
and identifies the conditions that would tip the decision.

State contract (RiskDebateState):
  IN  state['risk_debate_state'].aggressive_history
  IN  state['risk_debate_state'].conservative_history
  IN  state['risk_debate_state'].history
  OUT state['risk_debate_state'].neutral_history
  OUT state['risk_debate_state'].current_neutral_response
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_language_instruction

logger = logging.getLogger(__name__)


_NEU_SYSTEM = """You are the NEUTRAL risk analyst — a balanced, evidence-driven debator who weighs both aggressive and conservative perspectives.

Your role:
- Synthesize the aggressive and conservative arguments into a balanced view.
- Identify which arguments are data-supported and which are speculative.
- Propose a middle-ground position sizing and risk management approach.
- Clarify the key variables that would tip the decision toward aggression or caution.

Rules:
- Be specific: "The aggressive case hinges on 25% revenue growth, but Q3 showed deceleration to 12% — the conservative case is better supported here" is strong.
- If the Sharia report flags non-compliance, state plainly that Sharia compliance overrides risk/reward considerations — the stock should not be held.
- Do not split the difference for its own sake; if one side is clearly better supported by data, say so.
- Write in clear, professional prose. 2-3 paragraphs.
"""

_NEU_PROMPT = """## Instrument
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

## Conservative Debator's Arguments
{conservative_history}

## Combined Risk Debate Transcript
{debate_history}

## Your Task
Provide a balanced assessment. Weigh the aggressive and conservative arguments against the analyst data. Identify the key variables that should drive the final decision.
{language_instruction}"""


def create_neutral_risk_debator():
    """Return a LangGraph node function for the neutral risk debator."""
    quick_llm = get_quick_llm()

    def neutral_debator(state: Mapping[str, Any]) -> dict:
        debate = state.get("risk_debate_state") or {}
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")

        prompt = _NEU_PROMPT.format(
            instrument_context=instrument_context,
            trader_proposal=state.get("trader_investment_plan", "[No trader proposal available]"),
            market_report=state.get("market_report", "[Not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Not available]"),
            news_report=state.get("news_report", "[Not available]"),
            sharia_report=state.get("sharia_report", "[Not available]"),
            aggressive_history=debate.get("aggressive_history", "") or "(No aggressive arguments yet.)",
            conservative_history=debate.get("conservative_history", "") or "(No conservative arguments yet.)",
            debate_history=debate.get("history", "") or "(Risk debate is just beginning.)",
            language_instruction=get_language_instruction(),
        )

        logger.info("Neutral risk debator generating argument")
        response = quick_llm.invoke([
            HumanMessage(content=_NEU_SYSTEM),
            HumanMessage(content=prompt),
        ])
        argument = response.content.strip()

        # Update histories
        prev_neu = debate.get("neutral_history", "") or ""
        new_neu_history = f"{prev_neu}\n\n--- Neutral Turn ---\n{argument}".strip() if prev_neu else argument
        prev_combined = debate.get("history", "") or ""
        if prev_combined and prev_combined != "(Risk debate is just beginning.)":
            new_combined = f"{prev_combined}\n\n### Neutral\n{argument}"
        else:
            new_combined = f"### Neutral\n{argument}"

        return {
            "risk_debate_state": {
                **debate,
                "neutral_history": new_neu_history,
                "current_neutral_response": argument,
                "latest_speaker": "neutral",
                "history": new_combined,
                "count": debate.get("count", 0) + 1,
            }
        }

    return neutral_debator
