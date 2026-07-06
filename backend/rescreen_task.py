"""Background task: re-screen stocks for Sharia compliance drift.

Periodically fetches live market data for all stocks, recalculates the
AAOIFI financial ratios with updated market caps, and flags any stocks
whose compliance verdict has changed. Notifies users who watchlist
affected stocks via email.

Designed to run as a cron job or background task:
    python3 -m rescreen_task           # one-shot run
    python3 -m rescreen_task --loop    # continuous loop (60 min interval)

The task is fail-soft: any error in fetching a single stock is logged
and the task continues with the next stock.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

# Add backend dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sharia_screener import screen_company
from stock_data import get_price

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

STOCKS_PATH = Path(__file__).resolve().parent / "stocks.json"
LOOP_INTERVAL_SECONDS = 3600  # 1 hour


def load_stocks() -> list[dict]:
    """Load the current stock database."""
    if not STOCKS_PATH.exists():
        logger.error(f"stocks.json not found at {STOCKS_PATH}")
        return []
    with open(STOCKS_PATH) as f:
        return json.load(f)


def save_stocks(stocks: list[dict]) -> None:
    """Save the updated stock database."""
    with open(STOCKS_PATH, "w") as f:
        json.dump(stocks, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(stocks)} stocks to {STOCKS_PATH}")


def rescreen_stock(stock: dict) -> dict | None:
    """Re-screen a single stock with live price data.
    
    Returns the updated stock dict if the verdict changed, None otherwise.
    """
    ticker = stock.get("ticker", "")
    if not ticker:
        return None
    
    # Fetch live price
    price_data = get_price(ticker)
    if not price_data:
        return None
    
    live_market_cap = price_data.get("market_cap") or price_data.get("marketCap")
    live_price = price_data.get("price")
    
    if not live_market_cap or live_market_cap <= 0:
        # Can't re-screen without market cap
        return None
    
    # Store old verdict
    old_verdict = stock.get("verdict", "")
    old_market_cap = stock.get("market_cap", 0)
    
    # Update market cap with live data
    stock["market_cap"] = live_market_cap
    stock["last_updated"] = date.today().isoformat()
    
    # Re-run Sharia screen with updated market cap
    result = screen_company(
        name=stock.get("name_en", ticker),
        ticker=ticker,
        sector=stock.get("sector_en", ""),
        total_assets=stock.get("total_assets", 0),
        total_debt=stock.get("total_debt", 0),
        interest_bearing_investments=stock.get("interest_bearing_investments", 0),
        accounts_receivable=stock.get("accounts_receivable", 0),
        cash_and_equivalents=stock.get("cash_and_equivalents", 0),
        market_cap=live_market_cap,
        non_compliant_income=stock.get("non_compliant_income", 0),
        total_revenue=stock.get("total_revenue", 0),
    )
    
    new_verdict = result["verdict"]
    
    # Check if verdict changed
    if old_verdict and new_verdict != old_verdict:
        logger.warning(
            f"VERDICT CHANGED: {ticker} ({stock.get('name_en','')}) "
            f"{old_verdict} → {new_verdict}"
        )
        stock["verdict"] = new_verdict
        stock["verdict_detail"] = result["verdict_detail"]
        return stock
    
    # Always update verdict (in case it was missing)
    stock["verdict"] = new_verdict
    stock["verdict_detail"] = result["verdict_detail"]
    
    # Log significant market cap changes
    if old_market_cap and live_market_cap:
        pct_change = ((live_market_cap - old_market_cap) / old_market_cap) * 100
        if abs(pct_change) > 10:
            logger.info(
                f"  {ticker}: market cap {old_market_cap/1e9:.2f}B → "
                f"{live_market_cap/1e9:.2f}B ({pct_change:+.1f}%)"
            )
    
    return None  # No verdict change


def notify_users_of_change(ticker: str, old_verdict: str, new_verdict: str, stock: dict):
    """Send email notifications to users who watchlist a stock whose verdict changed.
    
    Fail-soft: never raise — logging only on email failures.
    """
    try:
        from database import SessionLocal
        from models import User, WatchlistItem
        from email_service import send_alert_notification_email
        
        db = SessionLocal()
        try:
            # Find all users watching this stock
            watchers = (
                db.query(WatchlistItem)
                .filter(WatchlistItem.ticker == ticker)
                .all()
            )
            
            if not watchers:
                return
            
            logger.info(f"  Notifying {len(watchers)} watchers of {ticker} verdict change")
            
            for item in watchers:
                user = item.user
                if not user or not user.email:
                    continue
                
                stock_name = stock.get("name_en", ticker)
                subject = f"Sharia Compliance Update: {stock_name} ({ticker})"
                body = (
                    f"The Sharia compliance status of {stock_name} ({ticker}) has changed:\n\n"
                    f"Previous: {old_verdict}\n"
                    f"Current: {new_verdict}\n\n"
                    f"Details: {stock.get('verdict_detail', '')}\n\n"
                    f"Please review your watchlist at mizan-invest.com/watchlist"
                )
                
                try:
                    send_alert_notification_email(user.email, subject, body, user.full_name)
                except Exception as e:
                    logger.warning(f"  Failed to email {user.email}: {e}")
                    
                # Update watchlist item verdict
                item.verdict = new_verdict
            
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"  Notification failed (fail-soft): {e}")


def run_rescreen():
    """Run one re-screening pass over all stocks."""
    logger.info(f"Starting re-screening at {datetime.now().isoformat()}")
    
    stocks = load_stocks()
    if not stocks:
        return
    
    logger.info(f"Loaded {len(stocks)} stocks from stocks.json")
    
    changes = 0
    errors = 0
    
    for i, stock in enumerate(stocks, 1):
        ticker = stock.get("ticker", f"#{i}")
        try:
            old_verdict = stock.get("verdict", "")
            updated = rescreen_stock(stock)
            
            if updated and old_verdict and old_verdict != updated.get("verdict", ""):
                changes += 1
                notify_users_of_change(ticker, old_verdict, updated["verdict"], updated)
            
            # Rate limit
            time.sleep(0.2)
            
        except Exception as e:
            errors += 1
            logger.warning(f"  {ticker}: error — {e}")
            continue
    
    # Save updated stocks
    save_stocks(stocks)
    
    logger.info(
        f"Re-screening complete: {len(stocks)} stocks, "
        f"{changes} verdict changes, {errors} errors"
    )


def main():
    parser = argparse.ArgumentParser(description="Re-screen stocks for Sharia compliance drift")
    parser.add_argument("--loop", action="store_true", help="Run continuously (1 hour interval)")
    args = parser.parse_args()
    
    if args.loop:
        logger.info(f"Starting continuous loop (interval={LOOP_INTERVAL_SECONDS}s)")
        while True:
            try:
                run_rescreen()
            except Exception as e:
                logger.error(f"Loop iteration failed: {e}")
            logger.info(f"Sleeping {LOOP_INTERVAL_SECONDS}s...")
            time.sleep(LOOP_INTERVAL_SECONDS)
    else:
        run_rescreen()


if __name__ == "__main__":
    main()
