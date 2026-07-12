"""AI Investment Research Engine.

Generates gold-standard investment research reports using LLMs via OpenRouter,
following the Buffett-Munger-Duan-Li Lu 4-master methodology (8-step framework).

Pipeline:
  1. Fetch financial data from Yahoo Finance (reuse stock_data.py)
  2. Build a comprehensive prompt encoding the 8-step methodology
  3. Call LLM API (DeepSeek V3 / GLM / any OpenRouter model)
  4. Parse response for rating + summary
  5. Store markdown report in ResearchReport

This is the core product: pure gold research reports.
"""

import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models import ResearchReport
from stock_data import get_price, get_price_history

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Fallback: load from ~/.kinox/env if not in environment (matches agent_pipeline/config.py)
if not OPENROUTER_API_KEY:
    _kinox_env = os.path.expanduser("~/.kinox/env")
    if os.path.exists(_kinox_env):
        with open(_kinox_env) as _f:
            for _line in _f:
                if _line.startswith("OPENROUTER_API_KEY="):
                    OPENROUTER_API_KEY = _line.split("=", 1)[1].strip()
                    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
                    break

# Default model: DeepSeek V4 Flash — fast, excellent reasoning, same one Hermes uses.
# Alternatives (set via RESEARCH_MODEL env var):
#   DeepSeek V4 Flash:  deepseek/deepseek-v4-flash
#   DeepSeek V3:        deepseek/deepseek-chat
#   DeepSeek R1:        deepseek/deepseek-r1
#   GLM:                zhipuai/glm-4.5
RESEARCH_MODEL = os.getenv("RESEARCH_MODEL", "deepseek/deepseek-v4-flash")
MAX_TOKENS = 16000
DAILY_REPORT_LIMIT = 5

# ── The Prompt: 4-Master Methodology ─────────────────────────────────────────
# This encodes the full investment-research skill framework:
#   Step 0: AI research bias self-check
#   Step 1: Data overview
#   Step 2: Business nature analysis (Duan Yongping — "the right business")
#   Step 3: Moat assessment (Buffett — "economic moat")
#   Step 4: Inverse thinking & risk checklist (Munger — "think backwards")
#   Step 5: Management assessment (Duan — "the right people" + Buffett integrity)
#   Step 6: Industry & civilization trends (Li Lu — "civilization framework")
#   Step 7: Valuation & margin of safety
#   Step 8: Final verdict & position sizing

SYSTEM_PROMPT = """You are an elite investment analyst combining the methodologies of four master investors: Warren Buffett, Charlie Munger, Duan Yongping (段永平), and Li Lu (李录).

You produce institutional-grade equity research reports in clean Markdown. Your analysis is rigorous, data-driven, and brutally honest. You identify both the bull and bear case with equal intensity. You never produce a report that could be written by reading a Wikipedia article — every report must contain original analytical insight.

Your reports follow an 8-step framework:
0. AI Research Bias Self-Check — assess information quality, flag cognitive biases
1. Data Overview — financial metrics, revenue structure, historical trends
2. Business Nature Analysis (Duan) — what is the "right business"? Moat analysis
3. Moat Assessment (Buffett) — 5 moat types, trend, durability over 10 years
4. Inverse Thinking & Risk (Munger) — how could this fail? Historical analogies
5. Management Assessment (Duan/Buffett) — capital allocation, integrity, succession
6. Industry & Civilization Trends (Li Lu) — is this a civilizational paradigm shift?
7. Valuation & Margin of Safety — multiple valuation approaches
8. Final Verdict — rating, position sizing, what would change the thesis"""

RESEARCH_PROMPT_TEMPLATE = """Research {company_name} ({ticker}).

## Live Market Data (from Yahoo Finance)
{financial_data}

## Historical Price Data
{price_history}

## Your Task

Produce a COMPLETE investment research report following the 8-step framework. Write in clear, professional English (or Arabic if this is a Saudi stock). Use Markdown tables for financial data. Be specific with numbers.

### CRITICAL REQUIREMENTS:

1. **Step 0 — AI Bias Self-Check**: Assess the information richness of this stock. Are we in a "consensus trap"? What are your own blind spots?

2. **Step 1 — Data Overview**: Present the financial data clearly. Calculate key ratios (P/E, P/B, P/S, EV/EBITDA, FCF yield, margins, growth rates). Cross-validate numbers where possible.

3. **Step 2 — Business Nature**: Define the business in one sentence. Is this "the right business"? What's the business model? Analyze margins and operating leverage.

4. **Step 3 — Moat Assessment**: Score each of the 5 moat types (brand/pricing power, switching costs, network effects, scale, tech/patents) from 1-5 stars. Is the moat widening or narrowing? What could destroy it in 10 years?

5. **Step 4 — Inverse Thinking**: List ALL ways this company could fail. Use historical analogies. Apply cross-disciplinary analysis (technology adoption curves, competitive dynamics, survivorship bias). Check for narrative bias and anchoring.

6. **Step 5 — Management**: Assess the CEO's track record on key decisions. Capital allocation skills. Insider ownership and recent transactions. Would the company survive without the founder?

7. **Step 6 — Industry & Civilization Trends**: Is this industry at a civilizational inflection point? Use Li Lu's framework — is this a 10-20 year secular trend or a cyclical play? Where on the S-curve?

8. **Step 7 — Valuation**: Calculate multiple valuation scenarios (base/bull/bear). What's the margin of safety at current prices? What price would represent a compelling entry?

9. **Step 8 — Final Verdict**: 

You MUST end the report with these exact lines (fill in your analysis):

**RATING: [exactly one of: STRONG_BUY | BUY | HOLD | WATCH | AVOID]**

**SUMMARY: [one sentence summary of the investment thesis]**

**TARGET_ENTRY: [price range or "N/A if current valuation is reasonable"]**

The rating and summary lines are REQUIRED — they are parsed by the system to populate the report metadata. Do not omit them."""

# ── Rating / summary parsing ─────────────────────────────────────────────────

_RATING_PATTERN = re.compile(
    r'\*\*(?:RATING|Rating):\s*\*?\\*?\s*(STRONG_BUY|BUY|HOLD|WATCH|AVOID)',
    re.IGNORECASE,
)
_SUMMARY_PATTERN = re.compile(
    r'\*\*SUMMARY:\s*\*?\*?\s*(.+?)(?:\n|\*\*TARGET)',
    re.DOTALL,
)
_COMPANY_NAME_PATTERN = re.compile(
    r'##\s*(?:Step 1|第一步).*?([A-Z][A-Za-z\s,&.]+)\s*(?:\(|（)',
    re.DOTALL,
)


def _parse_report_metadata(markdown: str) -> dict:
    """Extract rating and summary from the generated markdown report."""
    rating = None
    summary = None

    m = _RATING_PATTERN.search(markdown)
    if m:
        rating = m.group(1).upper()

    m = _SUMMARY_PATTERN.search(markdown)
    if m:
        summary = m.group(1).strip().strip('*').strip()
        # Clean up: remove trailing period if summary is one sentence
        if len(summary) > 300:
            summary = summary[:300].rsplit(' ', 1)[0] + "..."

    return {"rating": rating, "summary": summary}


# ── Financial data gathering ─────────────────────────────────────────────────

def _gather_financial_data(ticker: str) -> str:
    """Fetch live financial data and format as a context string for the LLM."""
    price_data = get_price(ticker)
    history = get_price_history(ticker, "6mo")

    lines = []

    if price_data:
        lines.append(f"- Current Price: {price_data.get('price', 'N/A')} {price_data.get('currency', '')}")
        lines.append(f"- Previous Close: {price_data.get('previous_close', 'N/A')}")
        if price_data.get('day_change_pct') is not None:
            lines.append(f"- Day Change: {price_data.get('day_change_pct')}%")
        lines.append(f"- 52-Week Range: {price_data.get('fifty_two_week_low', 'N/A')} - {price_data.get('fifty_two_week_high', 'N/A')}")
        lines.append(f"- Exchange: {price_data.get('exchange', 'N/A')}")
        lines.append(f"- Market State: {price_data.get('market_state', 'N/A')}")
        if price_data.get('volume'):
            lines.append(f"- Volume: {price_data.get('volume'):,}")
    else:
        lines.append("- [No live price data available for this ticker]")

    if history and len(history) > 1:
        # Calculate simple 6-month return
        first = history[0]["close"]
        last = history[-1]["close"]
        if first and last and first > 0:
            ret = ((last - first) / first) * 100
            lines.append(f"- 6-Month Return: {ret:.1f}%")
        lines.append(f"- 6-Month High: {max(h['close'] for h in history if h['close']):.2f}")
        lines.append(f"- 6-Month Low: {min(h['close'] for h in history if h['close']):.2f}")

    return "\n".join(lines)


def _gather_price_history_context(ticker: str) -> str:
    """Build a compact price-history table for the prompt."""
    history = get_price_history(ticker, "6mo")
    if not history or len(history) < 2:
        return "No price history available."

    # Sample: take ~12 evenly-spaced data points to keep prompt size manageable
    n = len(history)
    step = max(1, n // 12)
    sampled = history[::step][:12]

    lines = ["| Date | Close | Volume |", "|------|-------|--------|"]
    for h in sampled:
        date = h.get("date", "")
        close = h.get("close", "")
        vol = h.get("volume", "")
        if vol and isinstance(vol, (int, float)):
            vol = f"{int(vol):,}"
        lines.append(f"| {date} | {close} | {vol} |")

    return "\n".join(lines)


def _resolve_company_name(ticker: str) -> str:
    """Try to get the human-readable company name from stock_data."""
    try:
        info = get_price(ticker)
        if info and info.get("name"):
            return info["name"]
    except Exception:
        pass
    return ticker  # fallback: use the ticker as the name


# ── Rate limit check ─────────────────────────────────────────────────────────

def check_daily_rate_limit(user_id: int, db: Session) -> bool:
    """Return True if user has NOT exceeded their daily report limit."""
    cutoff = datetime.utcnow() - timedelta(hours=24)
    count = (
        db.query(ResearchReport)
        .filter(
            ResearchReport.user_id == user_id,
            ResearchReport.is_sample == False,
            ResearchReport.created_at >= cutoff,
        )
        .count()
    )
    return count < DAILY_REPORT_LIMIT


# ── Core engine: generate report ─────────────────────────────────────────────

def _call_llm(prompt: str) -> Optional[str]:
    """Call an LLM via OpenRouter (OpenAI-compatible API). Returns markdown or None."""
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not set — cannot generate research report")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
        response = client.chat.completions.create(
            model=RESEARCH_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        return content if content else None

    except Exception as e:
        logger.exception(f"LLM API call failed: {e}")
        return None


def generate_research_report(report_id: int) -> None:
    """Background task that generates a full research report.

    This function opens its own DB session (it runs outside the request lifecycle).
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
        if not report:
            logger.error(f"ResearchReport {report_id} not found")
            return

        # Update status to running
        report.status = "running"
        db.commit()

        ticker = report.ticker
        company_name = _resolve_company_name(ticker)
        report.company_name = company_name

        # ── Try the multi-agent pipeline first ────────────────────────────
        # If it fails, fall back to the single-LLM research engine.
        # Pipeline is enabled by default. Set USE_AGENT_PIPELINE=0 to
        # disable and use only the single-LLM engine.
        use_pipeline = os.getenv("USE_AGENT_PIPELINE", "1") != "0"
        
        if use_pipeline:
            try:
                from agent_pipeline import run_pipeline

                logger.info(f"Running multi-agent pipeline for {ticker} (report_id={report_id})")
                # Pipeline auto-detects sector/company/financials from yfinance
                result = run_pipeline(
                    ticker=ticker,
                    company_name=company_name,
                    report_id=report_id,
                )
                
                decision = result.get("decision", "")
                if decision and len(decision) > 200:
                    # Combine all agent reports into the final markdown
                    sections = []
                    if result.get("market_report"):
                        sections.append("## Market Analysis\n\n" + result["market_report"])
                    if result.get("fundamentals_report"):
                        sections.append("## Fundamentals Analysis\n\n" + result["fundamentals_report"])
                    if result.get("news_report"):
                        sections.append("## News & Macro Context\n\n" + result["news_report"])
                    if result.get("sharia_report"):
                        sections.append("## Sharia Compliance Analysis\n\n" + result["sharia_report"])
                    if result.get("investment_plan"):
                        sections.append("## Investment Plan (Bull/Bear Debate)\n\n" + result["investment_plan"])
                    if result.get("trader_investment_plan"):
                        sections.append("## Trader Proposal\n\n" + result["trader_investment_plan"])
                    sections.append("## Final Decision\n\n" + decision)
                    
                    markdown = "\n\n---\n\n".join(sections)
                    
                    # Parse metadata from the final decision
                    meta = _parse_report_metadata(decision)
                    if not meta.get("rating"):
                        # Try to extract rating from the structured decision
                        # Pipeline outputs: "Strong Buy", "Buy", "Hold", "Watch", "Avoid", "Non-Compliant"
                        rating_match = re.search(
                            r'\*\*Rating\*\*:\s*(Strong\s*Buy|Buy|Hold|Watch|Avoid|Non-Compliant)',
                            decision, re.IGNORECASE
                        )
                        if rating_match:
                            raw = rating_match.group(1).strip()
                            # Normalize: "Strong Buy" → "STRONG_BUY", "Non-Compliant" → "NON_COMPLIANT"
                            meta["rating"] = raw.upper().replace(" ", "_").replace("-", "_")
                        elif re.search(r'FINAL DECISION:\s*\*\*(NON-COMPLIANT)\*\*', decision, re.IGNORECASE):
                            meta["rating"] = "NON_COMPLIANT"
                        else:
                            meta["rating"] = "HOLD"
                    if not meta.get("summary"):
                        # Extract executive summary
                        summary_match = re.search(r'\*\*Executive Summary\*\*:\s*(.+?)(?:\n\n|\n\*\*|$)', decision, re.DOTALL)
                        if summary_match:
                            meta["summary"] = summary_match.group(1).strip()[:300]
                        else:
                            meta["summary"] = f"Multi-agent research report for {company_name}"
                    
                    report.report_markdown = markdown
                    report.rating = meta["rating"]
                    report.summary = meta["summary"]
                    report.status = "completed"
                    report.completed_at = datetime.utcnow()
                    db.commit()
                    logger.info(
                        f"Research report {report_id} completed via agent pipeline: "
                        f"{ticker} → {meta['rating']}"
                    )
                    return
                else:
                    logger.warning(f"Agent pipeline returned short result for {ticker}, falling back to single LLM")
            except Exception as e:
                logger.warning(f"Agent pipeline failed for {ticker} (report_id={report_id}): {e} — falling back to single LLM")
                import traceback
                traceback.print_exc()

        # ── Fallback: single-LLM research engine ────────────────────────────
        # Gather data
        financial_data = _gather_financial_data(ticker)
        price_history = _gather_price_history_context(ticker)

        # Build prompt
        prompt = RESEARCH_PROMPT_TEMPLATE.format(
            company_name=company_name,
            ticker=ticker,
            financial_data=financial_data,
            price_history=price_history,
        )

        logger.info(f"Generating research report for {ticker} (report_id={report_id}) using {RESEARCH_MODEL}")

        # Call LLM
        markdown = _call_llm(prompt)

        if markdown:
            # Parse metadata
            meta = _parse_report_metadata(markdown)
            report.report_markdown = markdown
            report.rating = meta["rating"]
            report.summary = meta["summary"]
            report.status = "completed"
            report.completed_at = datetime.utcnow()
            logger.info(
                f"Research report {report_id} completed: {ticker} → {meta['rating']}"
            )
        else:
            report.status = "failed"
            report.error = "AI research engine failed to generate report. Please try again."
            logger.error(f"Research report {report_id} failed: LLM returned no content")

        db.commit()

    except Exception as e:
        logger.exception(f"Research report {report_id} generation error: {e}")
        try:
            report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
            if report:
                report.status = "failed"
                report.error = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ── Sample report seeding ────────────────────────────────────────────────────

def seed_sample_reports(db: Session) -> None:
    """Seed demo/sample reports into the database if none exist.

    Uses the existing RKLB report as a high-quality sample.
    """
    existing = db.query(ResearchReport).filter(ResearchReport.is_sample == True).count()
    if existing > 0:
        return

    from pathlib import Path

    rklb_path = Path(__file__).resolve().parent.parent / "RKLB-investment-research.md"
    if not rklb_path.exists():
        logger.warning("RKLB sample report not found, skipping seed")
        return

    try:
        markdown = rklb_path.read_text(encoding="utf-8")
        meta = _parse_report_metadata(markdown)

        report = ResearchReport(
            user_id=None,
            ticker="RKLB",
            company_name="Rocket Lab USA",
            status="completed",
            report_markdown=markdown,
            rating=meta.get("rating", "WATCH"),
            summary=meta.get("summary") or "Space infrastructure play with strong moat but extreme valuation",
            is_sample=True,
            completed_at=datetime.utcnow(),
        )
        db.add(report)
        db.commit()
        logger.info("Seeded RKLB sample research report")
    except Exception as e:
        logger.warning(f"Failed to seed sample report: {e}")
