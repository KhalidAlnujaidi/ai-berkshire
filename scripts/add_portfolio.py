"""Patch backend/app.py to add portfolio screening endpoint."""

TARGET = "ai-berkshire/backend/app.py"

with open(TARGET, "r") as f:
    content = f.read()

if "portfolio-screen" in content:
    print("Already patched")
    exit(0)

# 1. Update docstring
content = content.replace(
    "  - GET  /api/search?q=...",
    "  - POST /api/portfolio-screen \u2014 screen an entire portfolio (multiple holdings)\n  - GET  /api/search?q=..."
)

# 2. Update version
content = content.replace('version="1.1.0"', 'version="1.2.0"')

# 3. Add models
old = "class StockBrief(BaseModel):"
new = '''
class PortfolioHolding(BaseModel):
    """A single holding in a portfolio screening request."""
    ticker: str = Field(..., description="Stock ticker symbol")
    amount: float = Field(..., gt=0, description="Investment amount in the holding's currency")


class PortfolioScreenRequest(BaseModel):
    """Request body for portfolio Sharia screening."""
    holdings: list[PortfolioHolding] = Field(..., min_length=1, description="Portfolio holdings")


class StockBrief(BaseModel):'''
content = content.replace(old, new)

# 4. Add endpoint
endpoint_code = '''
@app.post("/api/portfolio-screen")
async def screen_portfolio(req: PortfolioScreenRequest):
    """Screen an entire investment portfolio for Sharia compliance."""
    holdings_results = []
    total_amount = 0.0
    halal_amount = 0.0
    purification_amount = 0.0
    non_compliant_amount = 0.0
    not_found = []

    for holding in req.holdings:
        stock = find_stock(holding.ticker)
        if not stock:
            not_found.append(holding.ticker)
            continue

        result = screen_stock(stock)
        verdict = result.get("verdict", "NON_COMPLIANT")
        total_amount += holding.amount

        if verdict == "COMPLIANT":
            halal_amount += holding.amount
        elif verdict in ("COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"):
            halal_amount += holding.amount
            purification_amount += holding.amount
        else:
            non_compliant_amount += holding.amount

        holdings_results.append({
            "ticker": holding.ticker,
            "name_en": stock["name_en"],
            "name_ar": stock["name_ar"],
            "sector_en": stock["sector_en"],
            "sector_ar": stock["sector_ar"],
            "amount": holding.amount,
            "currency": stock.get("currency", "SAR"),
            "verdict": verdict,
            "verdict_ar": result.get("verdict_ar", ""),
            "verdict_detail": result.get("verdict_detail", ""),
            "is_halal": verdict in ("COMPLIANT", "COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"),
            "needs_purification": verdict in ("COMPLIANT_WITH_OVERLAY", "COMPLIANT_WITH_PURIFICATION"),
            "weight_pct": 0,
        })

    for h in holdings_results:
        h["weight_pct"] = round(h["amount"] / total_amount * 100, 2) if total_amount > 0 else 0

    halal_pct = round(halal_amount / total_amount * 100, 2) if total_amount > 0 else 0
    non_compliant_pct = round(non_compliant_amount / total_amount * 100, 2) if total_amount > 0 else 0
    purification_pct = round(purification_amount / total_amount * 100, 2) if total_amount > 0 else 0

    if non_compliant_pct > 50:
        grade = "HIGH_RISK"
        grade_ar = "\u0645\u062d\u0641\u0638\u0629 \u0639\u0627\u0644\u064a\u0629 \u0627\u0644\u0645\u062e\u0627\u0637\u0631"
    elif non_compliant_pct > 20:
        grade = "NEEDS_REBALANCING"
        grade_ar = "\u062a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u0625\u0639\u0627\u062f\u0629 \u062a\u0648\u0627\u0632\u0646"
    elif purification_pct > 30:
        grade = "PURIFICATION_REQUIRED"
        grade_ar = "\u064a\u0644\u0632\u0645 \u062a\u0646\u0642\u064a\u0629 \u0627\u0644\u062f\u062e\u0644"
    else:
        grade = "SHARIA_COMPLIANT"
        grade_ar = "\u0645\u062a\u0648\u0627\u0641\u0642\u0629 \u0645\u0639 \u0627\u0644\u0634\u0631\u064a\u0639\u0629"

    recommendations = []
    if non_compliant_amount > 0:
        nc_count = len([h for h in holdings_results if h["verdict"] == "NON_COMPLIANT"])
        recommendations.append({
            "type": "SELL",
            "title_en": f"Exit {nc_count} non-compliant holding(s)",
            "title_ar": f"\u062a\u062e\u0627\u0631\u062c \u0645\u0646 {nc_count} \u0627\u0633\u062a\u062b\u0645\u0627\u0631 \u063a\u064a\u0631 \u0645\u062a\u0648\u0627\u0641\u0642",
            "detail_en": f"{non_compliant_amount:,.0f} ({non_compliant_pct}%) of your portfolio is in non-compliant stocks.",
            "detail_ar": f"{non_compliant_amount:,.0f} ({non_compliant_pct}%) \u0645\u0646 \u0645\u062d\u0641\u0638\u062a\u0643 \u0641\u064a \u0623\u0633\u0647\u0645 \u063a\u064a\u0631 \u0645\u062a\u0648\u0627\u0641\u0642\u0629.",
            "severity": "critical",
        })
    if purification_amount > 0:
        pur_count = len([h for h in holdings_results if h["needs_purification"]])
        recommendations.append({
            "type": "PURIFY",
            "title_en": f"Purify income from {pur_count} holding(s)",
            "title_ar": f"\u0646\u0642\u0651 \u062f\u062e\u0644 {pur_count} \u0627\u0633\u062a\u062b\u0645\u0627\u0631",
            "detail_en": f"{purification_amount:,.0f} ({purification_pct}%) of your portfolio requires income purification.",
            "detail_ar": f"{purification_amount:,.0f} ({purification_pct}%) \u0645\u0646 \u0645\u062d\u0641\u0638\u062a\u0643 \u064a\u062a\u0637\u0644\u0628 \u062a\u0646\u0642\u064a\u0629 \u0627\u0644\u062f\u062e\u0644.",
            "severity": "warning",
        })
    if non_compliant_pct == 0 and purification_pct == 0:
        recommendations.append({
            "type": "GOOD",
            "title_en": "Your portfolio is fully Sharia-compliant",
            "title_ar": "\u0645\u062d\u0641\u0638\u062a\u0643 \u0645\u062a\u0648\u0627\u0641\u0642\u0629 \u0628\u0627\u0644\u0643\u0627\u0645\u0644 \u0645\u0639 \u0627\u0644\u0634\u0631\u064a\u0639\u0629",
            "detail_en": "All holdings pass both qualitative and quantitative Sharia screens.",
            "detail_ar": "\u062c\u0645\u064a\u0639 \u0627\u0644\u0627\u0633\u062a\u062b\u0645\u0627\u0631\u0627\u062a \u062a\u062c\u062a\u0627\u0632 \u0627\u0644\u0641\u062d\u0635\u064a\u0646 \u0627\u0644\u0646\u0648\u0639\u064a \u0648\u0627\u0644\u0643\u0645\u064a.",
            "severity": "success",
        })

    return {
        "holdings": holdings_results,
        "summary": {
            "total_holdings": len(holdings_results),
            "total_amount": total_amount,
            "halal_amount": halal_amount,
            "halal_pct": halal_pct,
            "non_compliant_amount": non_compliant_amount,
            "non_compliant_pct": non_compliant_pct,
            "purification_amount": purification_amount,
            "purification_pct": purification_pct,
            "grade": grade,
            "grade_ar": grade_ar,
        },
        "recommendations": recommendations,
        "not_found": not_found,
    }


'''

content = content.replace("\n@app.get(\"/api/search\")", endpoint_code + "\n@app.get(\"/api/search\")")

with open(TARGET, "w") as f:
    f.write(content)

print(f"Done: {len(content)} chars, {content.count(chr(10))} lines")
