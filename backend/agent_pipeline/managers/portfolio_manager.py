"""Portfolio Manager — the final decision node.

Reads the risk debate transcript, the trader's proposal, the Research
Manager's investment plan, and all four analyst reports, then uses the
**deep LLM** with structured output (``PortfolioDecision``) to produce
``state['final_trade_decision']`` — the pipeline's primary artifact.

The PortfolioDecision includes:
- Rating (6-tier Mizan scale)
- Executive summary
- Investment thesis
- Price target
- Confidence (High / Medium / Low)
- Key risks
- Sharia status + notes

This is the most important node in the pipeline. It synthesizes
everything into a single, actionable, Sharia-aware investment decision.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage

from agent_pipeline.llm import get_deep_llm
from agent_pipeline.schemas import PortfolioDecision, render_pm_decision
from agent_pipeline.structured import bind_structured, invoke_structured_or_freetext
from agent_pipeline.utils import get_language_instruction

logger = logging.getLogger(__name__)


_PM_SYSTEM = """You are the Portfolio Manager — the final decision-maker who synthesizes the entire analysis pipeline into a single investment verdict.

Your role:
1. Read all four analyst reports (market, fundamentals, news, Sharia).
2. Review the bull/bear debate and the Research Manager's investment plan.
3. Review the trader's proposal and the aggressive/conservative/neutral risk debate.
4. Issue the FINAL decision: rating, thesis, price target, confidence, key risks, and Sharia status.

This is the most consequential step. Your decision will be stored as the pipeline's output and presented to investors.

Critical rules:
- **Sharia override**: If the Sharia compliance report indicates non-compliance (failed qualitative or quantitative screen), your rating MUST be "Non-Compliant" and Sharia status MUST be "Non-Compliant". No financial attractiveness can override this.
- **Sharia with purification**: If the report says "Compliant with purification", set Sharia status accordingly and note the purification requirement.
- **Consistency**: Your rating must be consistent with the risk debate's consensus. If the conservative debator's concerns are well-supported, do not issue a Strong Buy.
- **Evidence-anchored**: Your investment thesis must reference specific data from the analyst reports and specific arguments from the debates. Generic statements are unacceptable.
- **Honesty**: If confidence is Low, say so. If key data is missing, note it. Investors respect honesty over false precision.
- **Price target**: Only provide a price target if you have sufficient data (current price + valuation metrics). Otherwise leave it null.
"""

_PM_PROMPT = """## Instrument
{instrument_context}

## ── Analyst Reports ──

### Market Analyst Report
{market_report}

### Fundamentals Analyst Report
{fundamentals_report}

### News & Macro Analyst Report
{news_report}

### Sharia Compliance Analyst Report
{sharia_report}

## ── Research Phase ──

### Research Manager's Investment Plan
{investment_plan}

### Trader's Transaction Proposal
{trader_proposal}

## ── Risk Debate ──

### Risk Debate Transcript
{risk_debate_history}

## ── Memory ──

### Past Analysis Context
{past_context}

## Your Task
Issue the FINAL investment decision. Provide:
1. **Rating**: Strong Buy / Buy / Hold / Watch / Avoid / Non-Compliant
2. **Executive Summary**: Action plan (entry, sizing, risk levels, horizon) in 2-4 sentences
3. **Investment Thesis**: Detailed reasoning anchored in the analyst reports and debates
4. **Price Target**: 12-month target if determinable
5. **Confidence**: High / Medium / Low
6. **Key Risks**: Top 2-3 risks that could invalidate the thesis
7. **Sharia Status**: Compliant / Compliant with purification / Non-Compliant

Remember: Sharia non-compliance overrides all financial considerations. If the Sharia report says non-compliant, the rating MUST be Non-Compliant.
{language_instruction}"""


def create_portfolio_manager():
    """Return a LangGraph node function for the Portfolio Manager.

    This is the most important node — it produces the final investment
    decision with rating, thesis, price target, confidence, key risks,
    and Sharia status.
    """
    deep_llm = get_deep_llm()
    structured_llm = bind_structured(deep_llm, PortfolioDecision, "portfolio_manager")

    def portfolio_manager(state: Mapping[str, Any]) -> dict:
        debate = state.get("risk_debate_state") or {}
        risk_debate_history = debate.get("history", "") or "(No risk debate transcript available.)"
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")
        past_context = state.get("past_context", "") or "(No past analysis context available.)"

        prompt = _PM_PROMPT.format(
            instrument_context=instrument_context,
            market_report=state.get("market_report", "[Market report not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Fundamentals report not available]"),
            news_report=state.get("news_report", "[News report not available]"),
            sharia_report=state.get("sharia_report", "[Sharia report not available]"),
            investment_plan=state.get("investment_plan", "[No investment plan available]"),
            trader_proposal=state.get("trader_investment_plan", "[No trader proposal available]"),
            risk_debate_history=risk_debate_history,
            past_context=past_context,
            language_instruction=get_language_instruction(),
        )

        logger.info("Portfolio Manager synthesizing final decision")
        final_trade_decision = invoke_structured_or_freetext(
            structured_llm,
            deep_llm,
            [HumanMessage(content=_PM_SYSTEM), HumanMessage(content=prompt)],
            render_pm_decision,
            "portfolio_manager",
        )

        # Store the judge's decision back into the risk debate state
        updated_debate = {**debate, "judge_decision": final_trade_decision}

        return {
            "final_trade_decision": final_trade_decision,
            "risk_debate_state": updated_debate,
        }

    return portfolio_manager
