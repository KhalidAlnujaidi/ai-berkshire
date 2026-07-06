"""Mizan analyst agents — four parallel-perspective analysts.

Each analyst reads pre-fetched data from the LangGraph state, invokes the
quick-think LLM, and writes a report field consumed by downstream bull/bear
researchers and the Research Manager.

Analysts:
- market_analyst      — technical / price-action read → ``market_report``
- fundamentals_analyst — 4-master methodology → ``fundamentals_report``
- news_analyst        — news & macro context → ``news_report``
- sharia_analyst      — AAOIFI Std 21 compliance → ``sharia_report``
"""

from agent_pipeline.analysts.fundamentals_analyst import fundamentals_analyst_node
from agent_pipeline.analysts.market_analyst import market_analyst_node
from agent_pipeline.analysts.news_analyst import news_analyst_node
from agent_pipeline.analysts.sharia_analyst import sharia_analyst_node

__all__ = [
    "market_analyst_node",
    "fundamentals_analyst_node",
    "news_analyst_node",
    "sharia_analyst_node",
]
