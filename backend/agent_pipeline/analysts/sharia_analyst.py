"""Sharia compliance analyst node for the Mizan pipeline.

Reads ``state['sharia_data']`` (produced by the deterministic
``sharia_screener`` wrapper in ``tools/data.py``) and produces an
interpretive report assessing AAOIFI Standard No. 21 compliance.
Writes ``state['sharia_report']``.

This analyst does **not** re-run the screening — the ratios and sector
verdict are computed deterministically upstream.  Its role is to:
  1. Interpret the screening results for non-expert downstream readers.
  2. Flag purification requirements (cleansing of impermissible income).
  3. Note data limitations that affect confidence in the verdict.
  4. Provide a clear compliance signal that the Portfolio Manager must
     honour: if this report says "Non-Compliant", the final decision
     must be rated Non-Compliant.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from agent_pipeline.llm import get_quick_llm
from agent_pipeline.utils import get_instrument_context_from_state, get_language_instruction

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Sharia compliance analyst specialising in AAOIFI Standard No. 21 (Screening of Sharia-Compliant Equities).

Your job: interpret the pre-computed Sharia screening results for a single instrument and produce a clear **Sharia compliance report**. The screening itself (sector classification + financial-ratio tests) is deterministic and has already been run — your role is interpretation, not recomputation.

Your report must cover:

1. **Compliance verdict**: State clearly one of:
   - **Compliant** — passes both qualitative (sector) and quantitative (ratio) screens.
   - **Compliant with purification** — passes screens but has impermissible income that must be purified (cleansed) by donating the non-compliant portion to charity.
   - **Non-Compliant** — fails the sector screen or one or more ratio thresholds. This is a hard fail: the stock cannot be held by Sharia-compliant funds.

2. **Screening details**: Summarise the sector classification and each ratio test result (debt-to-assets, interest-bearing investments, accounts receivable, cash, non-compliant income). For each, state whether it passed and the threshold.

3. **Purification guidance** (if applicable): If the stock is compliant but has non-compliant income, explain how purification works and the estimated percentage to cleanse.

4. **Data quality & confidence**: Note if financial data was incomplete (ratio screen skipped) and what that means for confidence in the verdict.

5. **Hard-fail escalation**: If the stock is Non-Compliant, state explicitly: "This stock is Non-Compliant under AAOIFI Standard 21. The Portfolio Manager must assign a Non-Compliant rating regardless of other factors."

The AAOIFI Standard 21 quantitative thresholds (for reference):
- Total interest-bearing debt / total assets ≤ 33%
- Total interest-bearing investments / total assets ≤ 33%
- Total accounts receivable / total assets ≤ 50%
- Total cash / total assets ≤ 33% (some scholars use a higher threshold)
- Non-compliant income / total revenue ≤ 5%

Be precise and authoritative. Downstream agents (Research Manager, Portfolio Manager) depend on your verdict as a **binding constraint** — if you say Non-Compliant, the final rating must be Non-Compliant."""


def sharia_analyst_node(state) -> dict:
    """Generate the Sharia compliance analyst report from screening data.

    Args:
        state: LangGraph ``AgentState`` with at least ``company_of_interest``
            and ``sharia_data`` populated.

    Returns:
        Dict update with ``sharia_report`` and a ``messages`` list containing
        the report as a ``HumanMessage``.
    """
    logger.info("Sharia analyst: starting analysis for %s", state.get("company_of_interest"))

    llm = get_quick_llm()
    ticker = state["company_of_interest"]
    instrument_ctx = get_instrument_context_from_state(state)
    lang_instruction = get_language_instruction()

    sharia_data = state.get("sharia_data", "[No Sharia screening data available]")

    human_content = (
        f"{instrument_ctx}\n\n"
        f"Assess the Sharia compliance of **{ticker}** under AAOIFI Standard No. 21.\n\n"
        f"## Sharia Screening Results\n{sharia_data}\n\n"
        f"Produce your Sharia compliance report now.{lang_instruction}"
    )

    prompt = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]

    response = llm.invoke(prompt)
    report = response.content

    logger.info("Sharia analyst: completed report for %s (%d chars)", ticker, len(report))

    return {
        "sharia_report": report,
        "messages": [HumanMessage(content=report)],
    }
