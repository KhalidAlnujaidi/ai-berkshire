#!/usr/bin/env python3
"""Generate sample research reports for the Mizan platform.

Uses the existing research_engine.py (single LLM call) to generate
high-quality investment research reports for display as public samples
on the Mizan platform (no auth required to view).

Usage:
    python3 generate_samples.py

The reports are saved to the database via the ResearchReport model,
with is_sample=True. They appear at /api/research/samples.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Load OpenRouter API key
env_path = Path.home() / ".kinox" / "env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            os.environ["OPENROUTER_API_KEY"] = line.split("=", 1)[1].strip()
            break

# Also set the model to DeepSeek v4-flash (cheap, fast, good quality)
os.environ.setdefault("RESEARCH_MODEL", "deepseek/deepseek-v4-flash")

# Add backend to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Stocks to generate sample reports for
SAMPLE_STOCKS = [
    {"ticker": "2222", "name": "Saudi Aramco", "sector": "Energy"},
    {"ticker": "1120", "name": "Al Rajhi Bank", "sector": "Islamic Banking"},
    {"ticker": "7010", "name": "STC Group", "sector": "Telecommunications"},
    {"ticker": "2010", "name": "SABIC", "sector": "Petrochemicals"},
    {"ticker": "1180", "name": "Saudi National Bank", "sector": "Conventional Banking"},
]


def generate_report(stock: dict) -> dict | None:
    """Generate a single research report using the research engine."""
    import research_engine
    
    ticker = stock["ticker"]
    name = stock["name"]
    sector = stock["sector"]
    
    logger.info(f"Generating report for {ticker} ({name})...")
    
    try:
        # Gather financial data
        financial_data = research_engine._gather_financial_data(ticker)
        price_history = research_engine._gather_price_history_context(ticker)
        
        # Build prompt
        prompt = research_engine.RESEARCH_PROMPT_TEMPLATE.format(
            company_name=name,
            ticker=ticker,
            financial_data=financial_data,
            price_history=price_history,
        )
        
        # Call the LLM (system prompt is inside _call_llm)
        markdown = research_engine._call_llm(prompt)
        
        if not markdown or len(markdown) < 500:
            logger.error(f"Report for {ticker} too short ({len(markdown or '')} chars)")
            return None
        
        # Parse metadata
        meta = research_engine._parse_report_metadata(markdown)
        
        result = {
            "ticker": ticker,
            "company_name": name,
            "report_markdown": markdown,
            "rating": meta.get("rating") or "WATCH",
            "summary": meta.get("summary") or f"Investment research report for {name}",
        }
        
        logger.info(f"  Generated {len(markdown)} chars, rating={result['rating']}")
        return result
        
    except Exception as e:
        logger.error(f"  Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_to_db(reports: list[dict]):
    """Save reports to the database as sample reports."""
    from database import engine, SessionLocal, Base
    from models import ResearchReport
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing samples
        db.query(ResearchReport).filter(ResearchReport.is_sample == True).delete()
        db.commit()
        
        for report in reports:
            db_report = ResearchReport(
                user_id=None,
                ticker=report["ticker"],
                company_name=report["company_name"],
                status="completed",
                report_markdown=report["report_markdown"],
                rating=report["rating"],
                summary=report["summary"],
                is_sample=True,
                completed_at=datetime.utcnow(),
            )
            db.add(db_report)
        
        db.commit()
        logger.info(f"Saved {len(reports)} sample reports to database")
    finally:
        db.close()


def main():
    logger.info(f"Generating {len(SAMPLE_STOCKS)} sample research reports...")
    
    reports = []
    for stock in SAMPLE_STOCKS:
        report = generate_report(stock)
        if report:
            reports.append(report)
    
    if not reports:
        logger.error("No reports generated — aborting")
        sys.exit(1)
    
    # Save to database
    save_to_db(reports)
    
    # Also save as markdown files for reference
    reports_dir = backend_dir.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    for report in reports:
        path = reports_dir / f"sample-{report['ticker']}-research.md"
        path.write_text(report["report_markdown"], encoding="utf-8")
        logger.info(f"Saved markdown to {path}")
    
    print(f"\n{'='*60}")
    print(f"  Generated {len(reports)} sample research reports")
    print(f"{'='*60}")
    for r in reports:
        print(f"  {r['ticker']}: {r['company_name']} | {r['rating']} | {len(r['report_markdown'])} chars")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
