#!/usr/bin/env python3
"""Sharia Compliance Screening Engine for AI Berkshire — Saudi Edition.

Deterministic Sharia compliance screening based on AAOIFI Standard No. 21.
This is the core differentiator of the Mizan SaaS platform: every stock must
pass BOTH qualitative (business activity) and quantitative (financial ratio)
screens to be deemed Sharia-compliant.

Zero external dependencies — uses only Python stdlib (decimal, json, argparse).
Requires Python >= 3.7.

Usage:
    python3 tools/sharia_screener.py screen \\
        --name "Al Rajhi Bank" \\
        --ticker 1120 \\
        --total-assets 500000 \\
        --total-debt 100000 \\
        --interest-bearing-investments 50000 \\
        --accounts-receivable 200000 \\
        --cash-and-equivalents 150000 \\
        --sector "Banking"

    python3 tools/sharia_screener.py batch-screen companies.json

    python3 tools/sharia_screener.py sector-check --sector "Alcohol"
    python3 tools/sharia_screener.py sector-check --sector "Banking"
    python3 tools/sharia_screener.py sector-check --sector "Technology"
"""

import argparse
import json
import sys
from decimal import Decimal, Context, ROUND_HALF_EVEN, InvalidOperation

# ---------------------------------------------------------------------------
# Exact Decimal Engine (same philosophy as financial_rigor.py)
# ---------------------------------------------------------------------------

_CTX = Context(prec=28, rounding=ROUND_HALF_EVEN)


def exact(value) -> Decimal:
    """Convert any numeric to exact Decimal, avoiding float traps."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(str(value))


def pct(numerator, denominator) -> Decimal:
    """Calculate percentage with exact decimal arithmetic."""
    num = exact(numerator)
    den = exact(denominator)
    if den == 0:
        return Decimal("0")
    return (_CTX.divide(num, den) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


# ---------------------------------------------------------------------------
# AAOIFI Standard No. 21 — Qualitative Screen (Business Activity)
# ---------------------------------------------------------------------------

# Non-compliant sectors: companies whose CORE business is prohibited.
# Key: case-insensitive substring match against the sector description.
# Two tiers: PERMITTED_WITH_OVERLAY (needs purification) vs PROHIBITED (hard fail).

HARAM_SECTORS = {
    # Conventional (non-Islamic) banking, insurance, and finance
    "conventional banking",
    "conventional insurance",
    "conventional finance",
    "interest-based finance",
    "riba-based",
    "conventional bank",
    "commercial bank",       # Western-style commercial banking
    "conventional insurer",

    # Alcohol
    "alcohol",
    "brewery",
    "distillery",
    "winery",
    "liquor",
    "spirits",

    # Pork / Non-Halal Meat
    "pork",
    "non-halal meat",
    "pig farming",
    "swine",

    # Gambling
    "gambling",
    "casino",
    "gaming (gambling)",   # distinguish from video game companies
    "lottery",
    "betting",

    # Tobacco
    "tobacco",
    "cigarette",
    "cigar",

    # Adult Entertainment
    "adult entertainment",
    "pornography",
    "adult content",

    # Weapons / Military (debated — some scholars allow defense, some prohibit)
    "weapons manufacturing",
    "nuclear weapons",
    "cluster munitions",
    "landmines",
}

# Sectors that are PERMITTED but may need earnings purification:
#   - Hotel chains that serve alcohol (purify alcohol revenue proportion)
#   - Conglomerates with mixed income (purify interest income proportion)
#   - Media companies with impermissible content segments
PERMITTED_WITH_OVERLAY = {
    "hospitality",         # hotels with alcohol sales
    "conglomerate",       # mixed business segments
    "media",              # may have impermissible segments
    "retail",             # supermarkets may sell alcohol/pork
    "diversified",        # diversified holdings
    "airlines",           # may serve alcohol
    "supermarket",
    "food retail",
}


def screen_sector(sector_name: str) -> dict:
    """Check if a business sector is Sharia-compliant.

    Returns dict with:
      - compliant: True/False
      - category: 'permitted' | 'permitted_with_overlay' | 'prohibited'
      - matched_rule: which rule triggered
      - notes: explanation
    """
    sector_lower = (sector_name or "").lower().strip()

    # Check prohibited sectors
    for haram in HARAM_SECTORS:
        if haram in sector_lower:
            return {
                "compliant": False,
                "category": "prohibited",
                "matched_rule": f"sector_match: '{haram}'",
                "notes": (
                    f"Core business ('{sector_name}') is in a prohibited sector. "
                    f"Sharia-compliant funds cannot hold this stock. "
                    f"This is a HARD FAIL — no purification possible."
                ),
            }

    # Check overlay sectors
    for overlay in PERMITTED_WITH_OVERLAY:
        if overlay in sector_lower:
            return {
                "compliant": True,
                "category": "permitted_with_overlay",
                "matched_rule": f"overlay_match: '{overlay}'",
                "notes": (
                    f"Sector ('{sector_name}') is permitted but may have impermissible "
                    f"revenue streams. Requires earnings purification if non-compliant "
                    f"income exceeds 5% of total revenue (AAOIFI Standard 21)."
                ),
            }

    # Default: permitted
    return {
        "compliant": True,
        "category": "permitted",
        "matched_rule": "default_permitted",
        "notes": "No prohibited sector match found. Passes qualitative screen.",
    }


# ---------------------------------------------------------------------------
# AAOIFI Standard No. 21 — Quantitative Screen (Financial Ratios)
# ---------------------------------------------------------------------------

# Thresholds per AAOIFI Standard No. 21 (widely adopted by Sharia scholars):
#   1. Total interest-bearing debt / Total market capitalization ≤ 33%
#      (Some scholars use total assets instead of market cap; we use both)
#   2. Total interest-bearing investments / Total market capitalization ≤ 33%
#   3. Accounts receivable / (Cash + Receivables) ≤ 50%
#      (Equivalently: illiquid assets / total assets ≥ a threshold)

RATIO_THRESHOLDS = {
    "debt_to_assets": Decimal("33.00"),          # %
    "debt_to_market_cap": Decimal("33.00"),      # %
    "interest_bearing_investments_to_assets": Decimal("33.00"),  # %
    "interest_bearing_investments_to_market_cap": Decimal("33.00"),  # %
    "receivables_to_total": Decimal("50.00"),    # % (cash + receivables)
    # Purification threshold
    "non_compliant_income_max": Decimal("5.00"),  # % of total revenue
}


def screen_ratios(
    total_assets: float,
    total_debt: float,
    interest_bearing_investments: float = 0,
    accounts_receivable: float = 0,
    cash_and_equivalents: float = 0,
    market_cap: float = 0,
    non_compliant_income: float = 0,
    total_revenue: float = 0,
) -> dict:
    """Run AAOIFI quantitative ratio screens.

    All monetary values should be in the SAME currency.
    Returns a dict with per-ratio pass/fail and overall verdict.
    """
    ta = exact(total_assets)
    td = exact(total_debt)
    ibi = exact(interest_bearing_investments or 0)
    ar = exact(accounts_receivable or 0)
    cash = exact(cash_and_equivalents or 0)
    mc = exact(market_cap or 0)
    nci = exact(non_compliant_income or 0)
    rev = exact(total_revenue or 0)

    results = {}
    all_pass = True

    # Ratio 1: Debt to Total Assets
    if ta > 0:
        r1 = pct(td, ta)
        passed = r1 <= RATIO_THRESHOLDS["debt_to_assets"]
        results["debt_to_assets"] = {
            "value": float(r1),
            "threshold": float(RATIO_THRESHOLDS["debt_to_assets"]),
            "passed": passed,
            "label": "Interest-bearing Debt / Total Assets",
        }
        if not passed:
            all_pass = False

    # Ratio 1b: Debt to Market Cap (if market cap provided)
    if mc > 0:
        r1b = pct(td, mc)
        passed = r1b <= RATIO_THRESHOLDS["debt_to_market_cap"]
        results["debt_to_market_cap"] = {
            "value": float(r1b),
            "threshold": float(RATIO_THRESHOLDS["debt_to_market_cap"]),
            "passed": passed,
            "label": "Interest-bearing Debt / Market Cap",
        }
        if not passed:
            all_pass = False

    # Ratio 2: Interest-bearing Investments to Total Assets
    if ta > 0:
        r2 = pct(ibi, ta)
        passed = r2 <= RATIO_THRESHOLDS["interest_bearing_investments_to_assets"]
        results["interest_bearing_investments_to_assets"] = {
            "value": float(r2),
            "threshold": float(RATIO_THRESHOLDS["interest_bearing_investments_to_assets"]),
            "passed": passed,
            "label": "Interest-bearing Investments / Total Assets",
        }
        if not passed:
            all_pass = False

    # Ratio 2b: Interest-bearing Investments to Market Cap
    if mc > 0:
        r2b = pct(ibi, mc)
        passed = r2b <= RATIO_THRESHOLDS["interest_bearing_investments_to_market_cap"]
        results["interest_bearing_investments_to_market_cap"] = {
            "value": float(r2b),
            "threshold": float(RATIO_THRESHOLDS["interest_bearing_investments_to_market_cap"]),
            "passed": passed,
            "label": "Interest-bearing Investments / Market Cap",
        }
        if not passed:
            all_pass = False

    # Ratio 3: Accounts Receivable / (Cash + Receivables)
    denom = cash + ar
    if denom > 0:
        r3 = pct(ar, denom)
        passed = r3 <= RATIO_THRESHOLDS["receivables_to_total"]
        results["receivables_to_total"] = {
            "value": float(r3),
            "threshold": float(RATIO_THRESHOLDS["receivables_to_total"]),
            "passed": passed,
            "label": "Accounts Receivable / (Cash + Receivables)",
        }
        if not passed:
            all_pass = False

    # Ratio 4: Non-compliant Income Ratio (purification check)
    if rev > 0:
        r4 = pct(nci, rev)
        passed = r4 <= RATIO_THRESHOLDS["non_compliant_income_max"]
        results["non_compliant_income"] = {
            "value": float(r4),
            "threshold": float(RATIO_THRESHOLDS["non_compliant_income_max"]),
            "passed": passed,
            "label": "Non-compliant Income / Total Revenue",
            "purification_needed": not passed,
            "purification_amount": float(nci) if not passed else 0,
        }
        # Non-compliant income doesn't cause hard fail, but requires purification
        # Only ratio 1-3 are hard fails

    results["_overall_quantitative"] = all_pass

    return results


# ---------------------------------------------------------------------------
# Combined Screen — Full Sharia Compliance Assessment
# ---------------------------------------------------------------------------

def screen_company(
    name: str,
    ticker: str = "",
    sector: str = "",
    total_assets: float = 0,
    total_debt: float = 0,
    interest_bearing_investments: float = 0,
    accounts_receivable: float = 0,
    cash_and_equivalents: float = 0,
    market_cap: float = 0,
    non_compliant_income: float = 0,
    total_revenue: float = 0,
) -> dict:
    """Run the full Sharia compliance screen: qualitative + quantitative.

    Returns a comprehensive verdict dict.
    """
    # --- Qualitative Screen ---
    sector_result = screen_sector(sector)

    # --- Quantitative Screen ---
    ratio_results = {}
    if total_assets > 0:
        ratio_results = screen_ratios(
            total_assets=total_assets,
            total_debt=total_debt,
            interest_bearing_investments=interest_bearing_investments,
            accounts_receivable=accounts_receivable,
            cash_and_equivalents=cash_and_equivalents,
            market_cap=market_cap,
            non_compliant_income=non_compliant_income,
            total_revenue=total_revenue,
        )

    # --- Final Verdict ---
    qualitative_pass = sector_result["compliant"]
    quantitative_pass = ratio_results.get("_overall_quantitative", True) if ratio_results else True

    if sector_result["category"] == "prohibited":
        verdict = "NON-COMPLIANT"
        verdict_ar = "غير متوافق"
        verdict_detail = "Prohibited business activity. Cannot be held by Sharia-compliant funds."
    elif not quantitative_pass:
        verdict = "NON-COMPLIANT"
        verdict_ar = "غير متوافق"
        verdict_detail = "Failed one or more financial ratio thresholds (AAOIFI Standard 21)."
    elif sector_result["category"] == "permitted_with_overlay":
        # Check if purification is needed
        nci_result = ratio_results.get("non_compliant_income", {})
        if nci_result.get("purification_needed"):
            verdict = "COMPLIANT_WITH_PURIFICATION"
            verdict_ar = "متوافق مع تطهير"
            verdict_detail = (
                "Permitted business but non-compliant income exceeds 5% threshold. "
                f"Purification required: donate {nci_result.get('purification_amount', 0):.2f} "
                "per share held to charity."
            )
        else:
            verdict = "COMPLIANT_WITH_OVERLAY"
            verdict_ar = "متوافق مع ملاحظات"
            verdict_detail = (
                "Permitted business. Monitor for impermissible income streams. "
                "May require earnings purification if non-compliant income > 5%."
            )
    else:
        verdict = "COMPLIANT"
        verdict_ar = "متوافق"
        verdict_detail = "Passes both qualitative and quantitative Sharia screens."

    return {
        "company": name,
        "ticker": ticker,
        "sector": sector,
        "verdict": verdict,
        "verdict_ar": verdict_ar,
        "verdict_detail": verdict_detail,
        "qualitative_screen": sector_result,
        "quantitative_screen": ratio_results if ratio_results else None,
        "standard": "AAOIFI Standard No. 21",
    }


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def print_report(result: dict):
    """Print a human-readable Sharia compliance report."""
    name = result["company"]
    ticker = result.get("ticker", "")
    sector = result.get("sector", "")
    verdict = result["verdict"]
    verdict_ar = result["verdict_ar"]

    icons = {
        "COMPLIANT": "✅",
        "COMPLIANT_WITH_OVERLAY": "✅⚠️",
        "COMPLIANT_WITH_PURIFICATION": "✅🤲",
        "NON-COMPLIANT": "❌",
    }
    icon = icons.get(verdict, "❓")

    print("=" * 70)
    print(f"  Sharia Compliance Screening Report")
    print(f"  تقرير الفحص الشرعي")
    print("=" * 70)
    print(f"  Company / الشركة:        {name} ({ticker})")
    print(f"  Sector / القطاع:          {sector}")
    print(f"  Standard / المعيار:       {result['standard']}")
    print()
    print(f"  Verdict / الحكم:          {icon} {verdict} — {verdict_ar}")
    print(f"  Detail:                   {result['verdict_detail']}")
    print()
    print("-" * 70)
    print("  Qualitative Screen / الفحص النوعي (Business Activity)")
    print("-" * 70)

    qs = result["qualitative_screen"]
    q_icons = {"permitted": "✅", "permitted_with_overlay": "⚠️", "prohibited": "❌"}
    print(f"    Category:   {q_icons.get(qs['category'], '?')} {qs['category']}")
    print(f"    Rule:       {qs['matched_rule']}")
    print(f"    Notes:      {qs['notes']}")
    print()

    if result.get("quantitative_screen"):
        print("-" * 70)
        print("  Quantitative Screen / الفحص الكمي (Financial Ratios)")
        print("-" * 70)

        qr = result["quantitative_screen"]
        for key, val in qr.items():
            if key.startswith("_"):
                continue
            if isinstance(val, dict) and "value" in val:
                p = "✅ PASS" if val["passed"] else "❌ FAIL"
                print(f"    {val['label']}")
                print(f"      {val['value']:.2f}% vs threshold {val['threshold']:.2f}% → {p}")
                if val.get("purification_needed"):
                    print(f"      🤲 Purification required: donate {val['purification_amount']:.2f} per share")
                print()

        overall = qr.get("_overall_quantitative")
        if overall is not None:
            o_icon = "✅" if overall else "❌"
            print(f"    Quantitative Overall: {o_icon} {'PASS' if overall else 'FAIL'}")
            print()

    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

def cmd_screen(args):
    """Screen a single company for Sharia compliance."""
    result = screen_company(
        name=args.name,
        ticker=args.ticker,
        sector=args.sector,
        total_assets=args.total_assets,
        total_debt=args.total_debt,
        interest_bearing_investments=args.interest_bearing_investments,
        accounts_receivable=args.accounts_receivable,
        cash_and_equivalents=args.cash_and_equivalents,
        market_cap=args.market_cap,
        non_compliant_income=args.non_compliant_income,
        total_revenue=args.total_revenue,
    )
    print_report(result)

    if args.json:
        print()
        print("--- JSON ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code: 0 = compliant, 1 = non-compliant (for automation)
    sys.exit(0 if "COMPLIANT" in result["verdict"] else 1)


def cmd_batch_screen(args):
    """Screen multiple companies from a JSON file.

    JSON format: [
      {"name": "...", "ticker": "...", "sector": "...", "total_assets": ..., ...},
      ...
    ]
    """
    with open(args.file, "r") as f:
        companies = json.load(f)

    results = []
    compliant = 0
    non_compliant = 0

    for company in companies:
        result = screen_company(**company)
        results.append(result)
        print_report(result)
        print()
        if "COMPLIANT" in result["verdict"]:
            compliant += 1
        else:
            non_compliant += 1

    print("=" * 70)
    print(f"  Batch Summary / ملخص الفحص الجماعي")
    print("=" * 70)
    print(f"  Total screened:    {len(results)}")
    print(f"  ✅ Compliant:      {compliant}")
    print(f"  ❌ Non-compliant:  {non_compliant}")
    print()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  Results saved to: {args.output}")

    sys.exit(0 if non_compliant == 0 else 1)


def cmd_sector_check(args):
    """Quick check if a sector is Sharia-compliant (qualitative only)."""
    result = screen_sector(args.sector)
    icons = {"permitted": "✅", "permitted_with_overlay": "⚠️", "prohibited": "❌"}
    icon = icons.get(result["category"], "?")
    print(f"\n  {icon} Sector: {args.sector}")
    print(f"  Category: {result['category']}")
    print(f"  Rule: {result['matched_rule']}")
    print(f"  Notes: {result['notes']}\n")
    sys.exit(0 if result["compliant"] else 1)


def cmd_list_standards(args):
    """Print the AAOIFI thresholds and rules being applied."""
    print("=" * 70)
    print("  AAOIFI Standard No. 21 — Screening Rules Applied")
    print("  معايير الأوراق المالية الإسلامية")
    print("=" * 70)
    print()
    print("  Qualitative Screen (Business Activity):")
    print("    ❌ Prohibited sectors:")
    for s in sorted(HARAM_SECTORS):
        print(f"       • {s}")
    print()
    print("    ⚠️ Permitted with overlay (may need purification):")
    for s in sorted(PERMITTED_WITH_OVERLAY):
        print(f"       • {s}")
    print()
    print("  Quantitative Screen (Financial Ratios):")
    for key, val in RATIO_THRESHOLDS.items():
        print(f"    • {key}: ≤ {val}%")
    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Sharia Compliance Screening Engine — AI Berkshire Saudi Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # screen subcommand
    p_screen = sub.add_parser("screen", help="Screen a single company")
    p_screen.add_argument("--name", required=True, help="Company name")
    p_screen.add_argument("--ticker", default="", help="Stock ticker")
    p_screen.add_argument("--sector", default="", help="Business sector")
    p_screen.add_argument("--total-assets", type=float, required=True, help="Total assets (currency units)")
    p_screen.add_argument("--total-debt", type=float, required=True, help="Total interest-bearing debt")
    p_screen.add_argument("--interest-bearing-investments", type=float, default=0)
    p_screen.add_argument("--accounts-receivable", type=float, default=0)
    p_screen.add_argument("--cash-and-equivalents", type=float, default=0)
    p_screen.add_argument("--market-cap", type=float, default=0)
    p_screen.add_argument("--non-compliant-income", type=float, default=0, help="Income from non-compliant activities")
    p_screen.add_argument("--total-revenue", type=float, default=0)
    p_screen.add_argument("--json", action="store_true", help="Also output JSON")
    p_screen.set_defaults(func=cmd_screen)

    # batch-screen subcommand
    p_batch = sub.add_parser("batch-screen", help="Screen multiple companies from JSON")
    p_batch.add_argument("file", help="Path to JSON file with company data array")
    p_batch.add_argument("--output", default="", help="Output JSON file path")
    p_batch.set_defaults(func=cmd_batch_screen)

    # sector-check subcommand
    p_sector = sub.add_parser("sector-check", help="Quick sector compliance check")
    p_sector.add_argument("--sector", required=True, help="Sector name to check")
    p_sector.set_defaults(func=cmd_sector_check)

    # standards subcommand
    p_std = sub.add_parser("standards", help="List AAOIFI screening rules")
    p_std.set_defaults(func=cmd_list_standards)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
