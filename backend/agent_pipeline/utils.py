"""Shared utilities for Mizan agent nodes.

Provides:
- get_language_instruction — output language for the final report
- build_instrument_context — deterministic ticker identity injection
- get_instrument_context_from_state — convenience accessor
- create_msg_delete — clears the message list between analysts
"""

from __future__ import annotations

import functools
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, RemoveMessage

from agent_pipeline import config


def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language."""
    lang = config.OUTPUT_LANGUAGE
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def build_instrument_context(
    ticker: str,
    company_name: str = "",
    sector: str = "",
) -> str:
    """Describe the exact instrument so agents preserve identity."""
    context = (
        f"The instrument to analyze is `{ticker}`. "
        "Use this exact ticker in every report and recommendation. "
    )

    details = []
    if company_name:
        details.append(f"Company: {company_name}")
    if sector:
        details.append(f"Sector: {sector}")

    if details:
        context += f"Resolved identity: {'; '.join(details)}."

    return context


def get_instrument_context_from_state(state: Mapping[str, Any]) -> str:
    """Return instrument context from state, falling back to ticker-only."""
    context = state.get("instrument_context")
    if isinstance(context, str) and context.strip():
        return context
    return build_instrument_context(str(state["company_of_interest"]))


def create_msg_delete():
    """Factory: returns a node that clears messages between analysts."""

    def delete_messages(state):
        messages = state["messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        ticker = state.get("company_of_interest", "the instrument")
        trade_date = state.get("trade_date", "the requested date")
        placeholder = HumanMessage(
            content=(
                f"Analysis of {ticker} as of {trade_date}. "
                "Continue with your assigned analysis task."
            )
        )
        return {"messages": removal_operations + [placeholder]}

    return delete_messages
