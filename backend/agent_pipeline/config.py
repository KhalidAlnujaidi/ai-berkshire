"""Mizan agent pipeline configuration.

All settings have env-var overrides so deployment (Render) and local dev
work identically.  Defaults match the existing research_engine.py settings.
"""

import os

# ── LLM settings (OpenRouter — OpenAI-compatible) ───────────────────────────

# Primary "deep thinking" model for the Research Manager and Portfolio
# Manager — the two nodes that make the final call.
DEEP_THINK_LLM = os.getenv("RESEARCH_MODEL", "deepseek/deepseek-chat")

# "Quick thinking" model for analysts, researchers, debators, trader.
# Same model is fine for Phase 1; can be swapped to a cheaper/faster one.
QUICK_THINK_LLM = os.getenv("RESEARCH_MODEL_QUICK", DEEP_THINK_LLM)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Fallback: load from ~/.kinox/env if not in environment
if not OPENROUTER_API_KEY:
    _kinox_env = os.path.expanduser("~/.kinox/env")
    if os.path.exists(_kinox_env):
        with open(_kinox_env) as _f:
            for _line in _f:
                if _line.startswith("OPENROUTER_API_KEY="):
                    OPENROUTER_API_KEY = _line.split("=", 1)[1].strip()
                    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
                    break
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Max tokens for non-structured analyst calls (analyst reports can be long).
MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "12000"))

# ── Pipeline behaviour ──────────────────────────────────────────────────────

# How many rounds of bull ↔ bear debate before the Research Manager decides.
MAX_DEBATE_ROUNDS = int(os.getenv("AGENT_MAX_DEBATE_ROUNDS", "1"))

# How many rounds of aggressive ↔ conservative ↔ neutral risk debate.
MAX_RISK_DISCUSS_ROUNDS = int(os.getenv("AGENT_MAX_RISK_ROUNDS", "1"))

# Output language for analyst reports and the final decision.
# Internal agent debate stays in English for reasoning quality.
OUTPUT_LANGUAGE = os.getenv("AGENT_OUTPUT_LANGUAGE", "English")

# ── Memory log ──────────────────────────────────────────────────────────────

# Stored as markdown alongside the DB for append-only atomic writes.
# Set to empty string to disable.
MEMORY_LOG_PATH = os.getenv(
    "AGENT_MEMORY_LOG_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "agent_memory.md"),
)

# Cap on resolved memory entries. None disables rotation.
MEMORY_LOG_MAX_ENTRIES = None

# ── Daily rate limiting (kept from research_engine.py) ──────────────────────

DAILY_REPORT_LIMIT = int(os.getenv("DAILY_REPORT_LIMIT", "5"))

# ── LangGraph recursion limit ───────────────────────────────────────────────

MAX_RECUR_LIMIT = int(os.getenv("AGENT_MAX_RECUR_LIMIT", "100"))


def build_config() -> dict:
    """Return a config dict for programmatic use."""
    return {
        "deep_think_llm": DEEP_THINK_LLM,
        "quick_think_llm": QUICK_THINK_LLM,
        "max_debate_rounds": MAX_DEBATE_ROUNDS,
        "max_risk_discuss_rounds": MAX_RISK_DISCUSS_ROUNDS,
        "output_language": OUTPUT_LANGUAGE,
        "memory_log_path": MEMORY_LOG_PATH,
        "memory_log_max_entries": MEMORY_LOG_MAX_ENTRIES,
        "max_recur_limit": MAX_RECUR_LIMIT,
        "max_tokens": MAX_TOKENS,
    }
