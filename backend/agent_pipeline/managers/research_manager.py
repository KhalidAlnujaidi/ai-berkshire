"""Research Manager.

Reads the bull ↔ bear debate transcript and all four analyst reports,
then uses the **deep LLM** with structured output (``ResearchPlan``) to
produce ``state['investment_plan']`` — a typed recommendation with
rationale and strategic actions for the trader.

This is the node that transitions the pipeline from debate to decision.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage

from agent_pipeline.llm import get_deep_llm
from agent_pipeline.schemas import ResearchPlan, render_research_plan
from agent_pipeline.structured import bind_structured, invoke_structured_or_freetext
from agent_pipeline.utils import get_language_instruction

logger = logging.getLogger(__name__)


_RM_SYSTEM = """You are the Research Manager — the senior analyst who adjudicates the bull/bear debate and issues the official investment plan.

Your role:
1. Weigh the bull and bear arguments against the analyst reports.
2. Determine which side's evidence is stronger and more data-anchored.
3. Issue a clear recommendation on Mizan's 6-tier scale: Strong Buy / Buy / Hold / Watch / Avoid / Non-Compliant.
4. Provide strategic actions for the trader (position sizing, entry/exit guidance).

Critical rules:
- If the Sharia compliance report indicates the stock is non-compliant (failed qualitative or quantitative screen), your recommendation MUST be "Non-Compliant" regardless of how attractive the financials are. Sharia non-compliance is a hard disqualifier.
- If the Sharia report indicates "Compliant with purification", you may proceed with a rating but note the purification requirement in your rationale.
- Your rationale must reference specific arguments from the debate — do not simply summarize.
- Be decisive. The trader needs a clear direction, not hedging.
"""

_RM_PROMPT = """## Instrument
{instrument_context}

## Market Analyst Report
{market_report}

## Fundamentals Analyst Report
{fundamentals_report}

## News & Macro Analyst Report
{news_report}

## Sharia Compliance Analyst Report
{sharia_report}

## Bull ↔ Bear Debate Transcript
{debate_transcript}

## Your Task
Adjudicate the debate. Issue your investment plan with:
- A recommendation (Strong Buy / Buy / Hold / Watch / Avoid / Non-Compliant)
- A rationale summarizing which debate arguments carried the decision
- Strategic actions for the trader (position sizing, entry/exit guidance)

Remember: if the Sharia report indicates non-compliance, the recommendation MUST be Non-Compliant.
{language_instruction}"""


def create_research_manager():
    """Return a LangGraph node function for the Research Manager."""
    deep_llm = get_deep_llm()
    structured_llm = bind_structured(deep_llm, ResearchPlan, "research_manager")

    def research_manager(state: Mapping[str, Any]) -> dict:
        debate = state.get("investment_debate_state") or {}
        debate_transcript = debate.get("history", "") or "(No debate transcript available.)"
        instrument_context = state.get("instrument_context") or state.get("company_of_interest", "the instrument")

        prompt = _RM_PROMPT.format(
            instrument_context=instrument_context,
            market_report=state.get("market_report", "[Market report not available]"),
            fundamentals_report=state.get("fundamentals_report", "[Fundamentals report not available]"),
            news_report=state.get("news_report", "[News report not available]"),
            sharia_report=state.get("sharia_report", "[Sharia report not available]"),
            debate_transcript=debate_transcript,
            language_instruction=get_language_instruction(),
        )

        logger.info("Research Manager adjudicating debate")
        investment_plan = invoke_structured_or_freetext(
            structured_llm,
            deep_llm,
            [HumanMessage(content=_RM_SYSTEM), HumanMessage(content=prompt)],
            render_research_plan,
            "research_manager",
        )

        # Store the judge's decision back into the debate state as well
        updated_debate = {**debate, "judge_decision": investment_plan}

        return {
            "investment_plan": investment_plan,
            "investment_debate_state": updated_debate,
        }

    return research_manager
