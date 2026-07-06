"""Agent state definitions for the Mizan LangGraph pipeline.

Adapted from TradingAgents' AgentState.  Key differences:
- No tool-call message accumulation (analysts pre-fetch data)
- Added Sharia-specific state fields
- Messages field kept for LangGraph MessagesState compatibility
"""

from typing import Annotated

from langgraph.graph import MessagesState
from typing_extensions import TypedDict


class InvestDebateState(TypedDict):
    """Bull ↔ bear debate state."""
    bull_history: Annotated[str, "Bullish argument history"]
    bear_history: Annotated[str, "Bearish argument history"]
    history: Annotated[str, "Combined debate history"]
    current_response: Annotated[str, "Latest response"]
    judge_decision: Annotated[str, "Research Manager's decision"]
    count: Annotated[int, "Debate turn count"]


class RiskDebateState(TypedDict):
    """Aggressive ↔ conservative ↔ neutral risk debate state."""
    aggressive_history: Annotated[str, "Aggressive analyst history"]
    conservative_history: Annotated[str, "Conservative analyst history"]
    neutral_history: Annotated[str, "Neutral analyst history"]
    history: Annotated[str, "Combined risk debate history"]
    latest_speaker: Annotated[str, "Analyst that spoke last"]
    current_aggressive_response: Annotated[str, "Latest aggressive response"]
    current_conservative_response: Annotated[str, "Latest conservative response"]
    current_neutral_response: Annotated[str, "Latest neutral response"]
    judge_decision: Annotated[str, "Portfolio Manager's decision"]
    count: Annotated[int, "Risk debate turn count"]


class AgentState(MessagesState):
    """Full pipeline state.

    Analysts write their reports here; downstream agents read them.
    The graph initialises every field before the first node runs.
    """
    # Instrument identity
    company_of_interest: Annotated[str, "Ticker symbol being analyzed"]
    trade_date: Annotated[str, "Analysis date (YYYY-MM-DD)"]

    # Analyst reports (each analyst fills its field)
    market_report: Annotated[str, "Market / technical analyst report"]
    fundamentals_report: Annotated[str, "Fundamentals analyst report"]
    news_report: Annotated[str, "News and macro analyst report"]
    sharia_report: Annotated[str, "Sharia compliance analyst report"]

    # Pre-fetched raw data (available to all agents via state)
    price_data: Annotated[str, "Formatted price/market data string"]
    financial_data: Annotated[str, "Formatted fundamentals data string"]
    news_data: Annotated[str, "Formatted news data string"]
    sharia_data: Annotated[str, "Sharia screening results string"]

    # Bull/bear debate
    investment_debate_state: Annotated[InvestDebateState, "Bull/bear debate state"]
    investment_plan: Annotated[str, "Research Manager's investment plan"]

    # Trader proposal
    trader_investment_plan: Annotated[str, "Trader's transaction proposal"]

    # Risk debate
    risk_debate_state: Annotated[RiskDebateState, "Risk debate state"]
    final_trade_decision: Annotated[str, "Portfolio Manager's final decision"]

    # Memory
    past_context: Annotated[str, "Past decision context from memory log"]
