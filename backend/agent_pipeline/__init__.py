"""Mizan Agent Pipeline — multi-agent investment analysis built on LangGraph.

Ported and adapted from TradingAgents (Tauric Research). Key differences:
- Pre-fetches data into prompts (no tool-calling loop) for reliability
- Adds a Sharia compliance analyst (AAOIFI Standard 21 screening)
- Configured for OpenRouter (OpenAI-compatible) via langchain-openai
- Uses Saudi market data sources (Tadawul + Yahoo Finance .SR suffix)

Pipeline:
    Market Analyst → Fundamentals Analyst → News Analyst → Sharia Analyst
        → Bull Researcher ↔ Bear Researcher (debate)
        → Research Manager → Trader
        → Aggressive ↔ Conservative ↔ Neutral (risk debate)
        → Portfolio Manager (final decision)
"""

from agent_pipeline.graph import build_graph, run_pipeline

__all__ = ["build_graph", "run_pipeline"]
