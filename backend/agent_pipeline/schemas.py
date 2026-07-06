"""Mizan-specific structured output schemas.

Adapted from TradingAgents' schemas.py with Sharia-specific additions.

These Pydantic models are used with ``llm.with_structured_output()`` so the
Research Manager, Trader, and Portfolio Manager produce typed, consistent
output across runs.  A render helper turns each parsed instance back into
markdown so downstream agents and the saved report consume the same shape.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

_NULLISH_FLOAT = {"", "none", "n/a", "na", "null", "nil", "-", "tbd", "unknown"}


def _coerce_optional_float(value):
    if isinstance(value, str) and value.strip().lower() in _NULLISH_FLOAT:
        return None
    return value


# ---------------------------------------------------------------------------
# Rating types — Mizan's 6-tier scale
# ---------------------------------------------------------------------------


class MizanRating(str, Enum):
    """6-tier rating scale (extends TradingAgents' 5-tier with a Sharia overlay)."""
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    AVOID = "Avoid"
    NON_COMPLIANT = "Non-Compliant"
    WATCH = "Watch"


class TraderAction(str, Enum):
    """Transaction direction."""
    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"


# ---------------------------------------------------------------------------
# Research Manager — investment plan after bull/bear debate
# ---------------------------------------------------------------------------


class ResearchPlan(BaseModel):
    """Structured investment plan produced by the Research Manager."""

    recommendation: MizanRating = Field(
        description=(
            "The investment recommendation. Exactly one of: Strong Buy / Buy / "
            "Hold / Watch / Avoid / Non-Compliant. If the Sharia screening found "
            "the stock non-compliant, set to Non-Compliant regardless of other factors."
        ),
    )
    rationale: str = Field(
        description=(
            "Summary of the bull/bear debate and which arguments carried the decision. "
            "2-4 sentences, conversational."
        ),
    )
    strategic_actions: str = Field(
        description=(
            "Concrete steps for the trader: position sizing, entry/exit guidance, "
            "consistent with the rating."
        ),
    )


def render_research_plan(plan: ResearchPlan) -> str:
    return "\n".join([
        f"**Recommendation**: {plan.recommendation.value}",
        "",
        f"**Rationale**: {plan.rationale}",
        "",
        f"**Strategic Actions**: {plan.strategic_actions}",
    ])


# ---------------------------------------------------------------------------
# Trader — transaction proposal
# ---------------------------------------------------------------------------


class TraderProposal(BaseModel):
    """Transaction proposal from the Trader."""

    action: TraderAction = Field(
        description="Transaction direction: Buy, Hold, or Sell.",
    )
    reasoning: str = Field(
        description="Case for this action, anchored in analyst reports. 2-4 sentences.",
    )
    entry_price: Optional[float] = Field(
        default=None, description="Optional entry price target.",
    )
    stop_loss: Optional[float] = Field(
        default=None, description="Optional stop-loss price.",
    )
    position_sizing: Optional[str] = Field(
        default=None, description="Optional sizing guidance, e.g. '5% of portfolio'.",
    )

    @field_validator("entry_price", "stop_loss", mode="before")
    @classmethod
    def _nullish_float_to_none(cls, v):
        return _coerce_optional_float(v)


def render_trader_proposal(proposal: TraderProposal) -> str:
    parts = [
        f"**Action**: {proposal.action.value}",
        "",
        f"**Reasoning**: {proposal.reasoning}",
    ]
    if proposal.entry_price is not None:
        parts.extend(["", f"**Entry Price**: {proposal.entry_price}"])
    if proposal.stop_loss is not None:
        parts.extend(["", f"**Stop Loss**: {proposal.stop_loss}"])
    if proposal.position_sizing:
        parts.extend(["", f"**Position Sizing**: {proposal.position_sizing}"])
    parts.extend(["", f"FINAL TRANSACTION PROPOSAL: **{proposal.action.value.upper()}**"])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Portfolio Manager — final decision (the main artifact)
# ---------------------------------------------------------------------------


class PortfolioDecision(BaseModel):
    """Final structured decision from the Portfolio Manager.

    This is the primary output of the pipeline. All fields are filled in a
    single LLM call via structured output.
    """

    rating: MizanRating = Field(
        description=(
            "Final rating. Exactly one of: Strong Buy / Buy / Hold / Watch / Avoid / "
            "Non-Compliant. If Sharia screening found the stock non-compliant, must "
            "be Non-Compliant."
        ),
    )
    executive_summary: str = Field(
        description=(
            "Concise action plan: entry strategy, position sizing, key risk levels, "
            "time horizon. 2-4 sentences."
        ),
    )
    investment_thesis: str = Field(
        description=(
            "Detailed reasoning anchored in the analysts' debate. Reference specific "
            "evidence from the reports."
        ),
    )
    price_target: Optional[float] = Field(
        default=None, description="12-month price target if determinable.",
    )
    confidence: str = Field(
        description="Confidence level: High, Medium, or Low.",
    )
    key_risks: str = Field(
        description="Top 2-3 risks that could invalidate the thesis.",
    )
    sharia_status: str = Field(
        description=(
            "Sharia compliance status: 'Compliant', 'Compliant with purification', "
            "or 'Non-Compliant'. Must be consistent with the Sharia analyst report."
        ),
    )
    sharia_notes: Optional[str] = Field(
        default=None,
        description="Specific Sharia compliance details (violations, purification needed, etc.).",
    )

    @field_validator("price_target", mode="before")
    @classmethod
    def _nullish_float_to_none(cls, v):
        return _coerce_optional_float(v)


def render_pm_decision(decision: PortfolioDecision) -> str:
    """Render PortfolioDecision to markdown for storage and downstream consumption."""
    parts = [
        f"**Rating**: {decision.rating.value}",
        "",
        f"**Executive Summary**: {decision.executive_summary}",
        "",
        f"**Investment Thesis**: {decision.investment_thesis}",
        "",
        f"**Confidence**: {decision.confidence}",
    ]
    if decision.price_target is not None:
        parts.extend(["", f"**Price Target**: {decision.price_target}"])
    parts.extend([
        "",
        f"**Key Risks**: {decision.key_risks}",
        "",
        f"**Sharia Status**: {decision.sharia_status}",
    ])
    if decision.sharia_notes:
        parts.extend(["", f"**Sharia Notes**: {decision.sharia_notes}"])
    parts.extend([
        "",
        f"FINAL DECISION: **{decision.rating.value.upper()}**",
    ])
    return "\n".join(parts)
