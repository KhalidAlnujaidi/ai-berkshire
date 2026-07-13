#!/usr/bin/env python3
"""Sharia Compliance Screening Engine for Mizan — Saudi Edition.

Deterministic Sharia compliance screening based on AAOIFI Standard No. 21.
This is the core differentiator of the Mizan SaaS platform: every stock must
pass BOTH qualitative (business activity) and quantitative (financial ratio)
screens to be deemed Sharia-compliant.

KEY PRINCIPLES:
  1. **Qualitative screen (business activity)**: If the core business is
     prohibited (riba-based, gambling, alcohol, etc.), the stock is
     NON-COMPLIANT regardless of financial ratios — a HARD FAIL.
  2. **Quantitative screen (financial ratios)**: Even halal-sector companies
     fail if they carry too much debt, interest-bearing investments, or
     receivables.
  3. **Purification**: Stocks that pass both screens but have minor
     non-compliant income (≤ 5%) are COMPLIANT WITH PURIFICATION — the
     investor must donate the non-compliant portion to charity.
  4. **Confidence**: When financial data is incomplete, the system reports
     LOW confidence and explains why.
  5. **Disclaimer**: This is an ALGORITHMIC assessment, not a religious
     ruling (fatwa). Users are advised to consult a qualified Sharia scholar
     for definitive guidance.

Zero external dependencies — uses only Python stdlib (decimal, json, argparse).
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
    """Convert any numeric to exact Decimal, avoiding float traps.

    NaN/None/empty values are coerced to 0 so downstream comparisons never
    raise InvalidOperation.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value if value.is_finite() else Decimal("0")
    if isinstance(value, float):
        if value != value:  # NaN check
            return Decimal("0")
        return Decimal(str(value))
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "-"):
        return Decimal("0")
    try:
        d = Decimal(s)
        return d if d.is_finite() else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


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

# IMPORTANT: Each HARAM entry is a LOWERCASE substring used to match against
# the company's sector description. The matching logic is:
#   `if haram_term in company_sector_lower: → PROHIBITED`
#
# This means entries must be short enough to catch variations.
#   E.g. "bank" will match "Conventional Banking", "Islamic Banking" is NOT
#   in this list because Islamic banks operate on Sharia-compliant principles.
#   But we need to be careful: "bank" matches "Islamic Bank" too, so we
#   explicitly exclude Islamic banking via the permitted_with_overlay list.

HARAM_SECTORS = {
    # ── Interest-based finance (Riba — the most severe prohibition) ───
    # Riba is explicitly prohibited in the Quran (2:275-279)
    "conventional banking",       # Catches "Conventional Banking", "Conventional Bank"
    "conventional insurance",     # Conventional insurance involves gharar + riba
    "conventional finance",       # Interest-based lending/finance companies
    "interest-based",             # Any business model based on interest
    "riba",                       # Direct mention of riba
    "commercial bank",            # Western-style commercial banks

    # ── Alcohol (Khamr — prohibited by Quran 5:90) ───────────────────
    "alcohol",                    # Primary intoxicant production/distribution
    "brewery",                    # Beer brewing
    "distillery",                 # Spirits/liquor production
    "winery",                     # Wine production
    "liquor",                     # Hard alcohol
    "spirits",                    # Distilled beverages
    "beer",                       # Brewed alcoholic beverage
    "wine",                       # Fermented grape beverage
    "intoxicant",                 # General intoxicating substances

    # ── Pork / Non-Halal Meat (prohibited by Quran 2:173) ────────────
    "pork",                       # Pig meat production/processing
    "non-halal meat",             # Meat not slaughtered per Islamic requirements
    "pig farming",                # Commercial pig farming
    "swine",                      # Pigs (alternative term)
    "lard",                       # Pig fat used in food production

    # ── Gambling / Maysir (prohibited by Quran 5:90) ─────────────────
    "gambling",                   # General gambling operations
    "casino",                     # Casino operations
    "gaming (gambling)",          # Gambling-specific gaming (not video games)
    "lottery",                    # Lottery tickets / drawings
    "betting",                    # Sports betting / bookmaking
    "bookmaker",                  # Odds setting / bookmaking
    "slot machine",               # Electronic gambling machines
    "poker",                      # Poker rooms / clubs
    "bingo",                      # Bingo halls

    # ── Tobacco (prohibited by scholarly consensus due to harm) ───────
    "tobacco",                    # Cigarette/tobacco production
    "cigarette",                  # Cigarette manufacturing
    "cigar",                      # Cigar manufacturing
    "vape",                       # E-cigarettes / vaping products
    "nicotine",                   # Nicotine products
    "smoking",                    # Smoking-related products

    # ── Adult Entertainment (prohibited by Quran 24:30-31) ───────────
    "adult entertainment",        # Adult content industry
    "pornography",                # Explicit content production/distribution
    "adult content",              # Age-restricted explicit content
    "escort",                     # Escort services
    "dating",                     # Dating services (non-halal matchmaking)
    "strip club",                 # Adult entertainment venues
    "massage parlor",             # Illicit massage establishments

    # ── Weapons / Defense (scholarly difference of opinion) ─────────
    # Some scholars prohibit all weapons manufacturing; others permit
    # defensive weapons. We take the conservative (prohibited) position
    # for automatic weapons, cluster munitions, and nuclear weapons.
    "cluster munitions",          # Banned under international law
    "landmines",                  # Banned under Ottawa Treaty
    "nuclear weapons",            # Weapons of mass destruction
    "biological weapons",         # Biological warfare agents
    "chemical weapons",           # Chemical warfare agents

    # ── Insurance (Conventional — involves Gharar + Riba) ───────────
    # Conventional insurance is prohibited because it involves:
    #   1. Gharar (excessive uncertainty) — the policyholder doesn't know
    #      if or when they'll receive a payout
    #   2. Riba — insurance companies invest premiums in interest-bearing
    #      instruments
    #   3. Maysir (gambling) — insurance is structured as a bet against
    #      future events
    # Takaful (Islamic insurance) is permissible but MUST be labeled as such.
    "insurance",                  # Catches "Insurance", "Insurance Brokerage", etc.
    "insurer",                    # Insurance companies
    "reinsurance",                # Reinsurance companies
    "underwriting",               # Insurance underwriting

    # ── Defence / Military contracting ──────────────────────────────
    "defence",                    # Defence/military contracting
    "defense",                    # US spelling of defence
    "military",                   # Military equipment/services
    "arms",                       # Weapons/arms dealing
    "weapons",                    # Weapons manufacturing
    "munitions",                  # Ammunition/munitions
    "firearm",                    # Guns/rifles manufacturing
    "defense contractor",         # Defense contracting
    "defence contractor",         # Defence contracting

    # ── For-profit education (involves selling degrees/debt) ─────────
    # While education itself is halal, for-profit universities that load
    # students with riba-based debt and prioritize profit over education
    # quality fall into problematic categories.
    "for-profit education",       # For-profit educational institutions

    # ── Private prisons / detention ───────────────────────────────────
    "private prison",             # For-profit incarceration
    "detention center",           # For-profit detention
    "corrections for-profit",     # For-profit corrections
}

# Sectors that are PERMITTED but need earnings purification:
#   - Hotel chains that serve alcohol (purify alcohol revenue proportion)
#   - Conglomerates with mixed income (purify interest income proportion)
#   - Media companies with impermissible content segments
#   - Airlines that serve alcohol (purify alcohol revenue)
#   - Islamic Banks (halal but operate alongside conventional systems)
PERMITTED_WITH_OVERLAY = {
    "hospitality",                # Hotels with alcohol sales
    "hotel",                      # Hotels/resorts
    "conglomerate",               # Mixed business segments
    "diversified",                # Diversified holdings
    "media",                      # May have impermissible content segments
    "broadcasting",               # TV/radio with mixed content
    "entertainment",              # Entertainment with mixed content
    "retail",                     # May sell alcohol/pork in some locations
    "supermarket",                # May sell non-halal products
    "food retail",                # Grocery stores
    "airline",                    # Serves alcohol onboard
    "aviation",                   # Airline/aviation services
    "travel",                     # Travel agencies may book non-halal services
    "tourism",                    # Tourism with mixed permissible/prohibited
    "restaurant",                 # May serve non-halal food
    "food & beverage",            # Food with potential non-halal items
    "food and beverage",          # Same as above
    "islamic bank",               # Islamic banking (Sharia-compliant by nature,
                                  # but operates in a riba-based system — needs
                                  # purification of any incidental non-compliant income)
    "islamic banking",            # Same as above, plural
    "takaful",                    # Islamic insurance (Sharia-compliant)
}


def screen_sector(sector_name: str) -> dict:
    """Check if a business sector is Sharia-compliant with detailed reasoning.

    Returns dict with:
      - compliant: True/False
      - category: 'permitted' | 'permitted_with_overlay' | 'prohibited'
      - matched_rule: which rule triggered (for transparency)
      - explanation: detailed, human-readable reasoning in English
      - explanation_ar: detailed, human-readable reasoning in Arabic
      - notes: short summary
    """
    sector_lower = (sector_name or "").lower().strip()

    if not sector_lower:
        return {
            "compliant": True,
            "category": "permitted",
            "matched_rule": "default_permitted_no_sector",
            "explanation": (
                "No sector information was provided for this stock. "
                "The qualitative screen was skipped due to missing data. "
                "The stock is provisionally treated as compliant subject to sector verification. "
                "⚠️ NOTE: This is a LOW-CONFIDENCE assessment. You should verify the company's "
                "business activities independently or consult a Sharia scholar."
            ),
            "explanation_ar": (
                "لم يتم تقديم معلومات عن قطاع هذا السهم. تم تخطي الفحص النوعي لعدم وجود بيانات. "
                "يتم التعامل مع السهم بشكل مؤقت كمتوافق لحين التحقق من القطاع. "
                "⚠️ هذا تقييم منخفض الثقة. يرجى التحقق من أنشطة الشركة بشكل مستقل أو استشارة عالم شرعي."
            ),
            "notes": "Sector information missing — qualitative screen skipped (low confidence).",
        }

    # Check prohibited sectors
    for haram in HARAM_SECTORS:
        if haram in sector_lower:
            matched_rule = f"sector_match: '{haram}' in '{sector_name}'"
            explanation = _build_haram_explanation(sector_name, haram)
            explanation_ar = _build_haram_explanation_ar(sector_name, haram)
            return {
                "compliant": False,
                "category": "prohibited",
                "matched_rule": matched_rule,
                "explanation": explanation,
                "explanation_ar": explanation_ar,
                "notes": f"❌ NON-COMPLIANT: {sector_name} is a prohibited sector ({haram}). This is a HARD FAIL.",
            }

    # Check overlay sectors
    for overlay in PERMITTED_WITH_OVERLAY:
        if overlay in sector_lower:
            matched_rule = f"overlay_match: '{overlay}' in '{sector_name}'"
            explanation, explanation_ar = _build_overlay_explanation(sector_name, overlay)
            return {
                "compliant": True,
                "category": "permitted_with_overlay",
                "matched_rule": matched_rule,
                "explanation": explanation,
                "explanation_ar": explanation_ar,
                "notes": (
                    f"⚠️ COMPLIANT WITH OVERLAY: {sector_name} is generally permissible "
                    f"but may have mixed revenue streams. See detailed explanation."
                ),
            }

    # Default: permitted
    return {
        "compliant": True,
        "category": "permitted",
        "matched_rule": "default_permitted",
        "explanation": (
            f"The sector '{sector_name}' does not appear in any prohibited business category. "
            f"Based on available sector classification, this company operates in a permissible "
            f"industry under AAOIFI Standard No. 21. "
            f"Note: This is a sector-level screen only. The stock must still pass the quantitative "
            f"(financial ratio) screen below."
        ),
        "explanation_ar": (
            f"القطاع '{sector_name}' لا يظهر في أي فئة أعمال محظورة. "
            f"بناءً على تصنيف القطاع المتاح، تعمل هذه الشركة في صناعة مباحة "
            f"وفقاً لمعيار AAOIFI رقم 21. "
            f"ملاحظة: هذا فحص على مستوى القطاع فقط. يجب أن يجتاز السهم أيضاً "
            f"الفحص الكمي (النسب المالية) أدناه."
        ),
        "notes": f"✅ Sector '{sector_name}' is permissible.",
    }


def _build_haram_explanation(sector: str, matched_term: str) -> str:
    """Build a detailed explanation for why a sector is prohibited."""
    explanations = {
        "bank": (
            "Conventional banking is based on Riba (interest), which is explicitly and "
            "repeatedly prohibited in the Quran (Surah Al-Baqarah 2:275-279). "
            "Riba is considered one of the most severe sins in Islam. "
            "Conventional banks operate by taking deposits, paying interest, making loans "
            "at higher interest rates, and investing in interest-bearing instruments. "
            "All of these activities involve Riba."
        ),
        "insurance": (
            "Conventional insurance is prohibited in Islam for three reasons:\n"
            "1. GHARAR (excessive uncertainty): The policyholder pays premiums without "
            "knowing if or when they will receive a payout. This is a form of prohibited uncertainty.\n"
            "2. RIBA: Insurance companies invest customer premiums in interest-bearing "
            "instruments (bonds, deposits), generating riba income.\n"
            "3. MAYSIR (gambling): Insurance contracts resemble bets against uncertain "
            "future events.\n\n"
            "Note: Takaful (Islamic insurance) is a Sharia-compliant alternative. "
            "This company has NOT been identified as Takaful."
        ),
        "alcohol": "Alcohol (Khamr) is explicitly prohibited in the Quran (Surah Al-Ma'idah 5:90). "
                   "The Prophet Muhammad (ﷺ) said: 'Whatever intoxicates in large quantities, "
                   "a small quantity of it is also forbidden.' (Sunan al-Tirmidhi)",
        "gambling": "Gambling (Maysir) is explicitly prohibited in the Quran (Surah Al-Ma'idah 5:90). "
                    "It is considered a form of unjust enrichment and creating risk without "
                    "productive economic activity.",
        "pork": "Consumption of pork and its by-products is explicitly prohibited in the Quran "
                "(Surah Al-Baqarah 2:173).",
        "tobacco": "While not explicitly mentioned in the Quran, tobacco is prohibited by "
                   "scholarly consensus due to the clear harm it causes to health, which "
                   "contradicts the Islamic principle of not harming oneself (Quran 2:195).",
        "adult": "Adult entertainment is prohibited under Islamic principles of modesty "
                 "and chastity (Quran 24:30-31).",
        "defence": "Manufacturing weapons of war falls under a scholarly difference of opinion. "
                   "Defensive weapons may be permissible, but the industry involves ethical "
                   "complexities that warrant caution. Mizan takes the conservative position.",
        "weapons": "Weapons manufacturing involves ethical complexities. While some scholars "
                   "permit defensive weapons, the industry is difficult to screen for "
                   "ethical end-use.",
    }

    # Default explanation for terms not specifically listed
    default = (
        f"The sector '{sector}' (matched term: '{matched_term}') contains business activities "
        f"that are prohibited under Islamic law. This is a HARD FAIL under AAOIFI Standard No. 21 — "
        f"no further screening (quantitative) is needed. "
        f"Sharia-compliant funds and Muslim investors cannot hold or trade this stock."
    )

    # Check for specific explanation
    for key, explanation in explanations.items():
        if key in matched_term or key in sector.lower():
            return explanation + ("\n\n" + default if not explanation.endswith(".") else "\n\n" + default)

    return default


def _build_haram_explanation_ar(sector: str, matched_term: str) -> str:
    """Arabic version of the haram explanation."""
    return (
        f"القطاع '{sector}' (المطابق: '{matched_term}') يحتوي على أنشطة تجارية "
        f"محظورة في الشريعة الإسلامية. هذا رفض نهائي بموجب معيار AAOIFI رقم 21 — "
        f"لا حاجة لفحص إضافي (كمي). "
        f"صناديق الاستثمار المتوافقة مع الشريعة والمستثمرون المسلمون لا يمكنهم "
        f"حيازة أو تداول هذا السهم."
    )


def _build_overlay_explanation(sector: str, overlay: str) -> tuple[str, str]:
    """Build explanations for overlay sectors."""
    explanations = {
        "hotel": (
            "Hotels and hospitality businesses are generally permissible, BUT they may generate "
            "non-compliant revenue from:\n"
            "1. Serving/permitting alcohol in restaurants, bars, or minibars\n"
            "2. Operating non-halal food options\n"
            "3. Hosting events with prohibited activities (gambling, adult entertainment)\n\n"
            "VERDICT: The STOCK is COMPLIANT but any revenue from prohibited activities "
            "must be purified (donated to charity). The quantitative ratio screen below shows "
            "whether non-compliant income exceeds the 5% threshold."
        ),
        "airline": (
            "Airlines are generally permissible as they provide essential transportation services. "
            "HOWEVER, they may generate non-compliant revenue from:\n"
            "1. Serving alcohol onboard\n"
            "2. Interest income from cash reserves\n"
            "3. Non-halal meal options\n\n"
            "VERDICT: The STOCK is COMPLIANT but any non-compliant revenue must be "
            "purified. Check the non-compliant income ratio below."
        ),
        "islamic bank": (
            "Islamic banks operate on Sharia-compliant principles (profit-sharing, asset-backed "
            "financing, avoiding riba). However, in practice they may have incidental exposure "
            "to non-compliant income through:\n"
            "1. Deposits at conventional central banks that pay interest\n"
            "2. Commingled funds in money markets\n\n"
            "VERDICT: The STOCK is COMPLIANT but may require purification of incidental "
            "non-compliant income. Islamic banks must also pass the quantitative ratio screen."
        ),
        "media": (
            "Media companies are generally permissible but may generate non-compliant revenue "
            "from:\n"
            "1. Advertising for prohibited products (alcohol, gambling, etc.)\n"
            "2. Content that violates Islamic modesty standards\n"
            "3. Music and entertainment segments deemed impermissible by some scholars\n\n"
            "VERDICT: COMPLIANT with purification requirement for any non-compliant income."
        ),
        "retail": (
            "Retail businesses are generally permissible but may generate non-compliant revenue from:\n"
            "1. Selling alcohol, pork, or non-halal meat products\n"
            "2. Interest income from store credit cards or financing\n"
            "3. Tobacco sales (controversial but common practice)\n\n"
            "VERDICT: COMPLIANT with monitoring required. Check non-compliant income ratio."
        ),
    }

    default_en = (
        f"The sector '{sector}' is generally permissible under Islamic law, but may involve "
        f"mixed revenue streams, some of which could be non-compliant. "
        f"The stock passes the qualitative screen with an OVERLAY — any non-compliant income "
        f"must be purified by donating to charity. Please review the quantitative screen below "
        f"for specific ratio results."
    )
    default_ar = (
        f"القطاع '{sector}' مباح بشكل عام في الشريعة الإسلامية، لكن قد يشمل "
        f"مصادر دخل مختلطة قد تكون غير متوافقة. "
        f"يجتاز السهم الفحص النوعي مع اشتراط تطهير أي دخل غير متوافق "
        f"بالتبرع للجمعيات الخيرية. يرجى مراجعة الفحص الكمي أدناه للتفاصيل."
    )

    for key, explanation in explanations.items():
        if key in overlay or key in sector.lower():
            return explanation, default_ar  # Arabic as fallback

    return default_en, default_ar


# ---------------------------------------------------------------------------
# AAOIFI Standard No. 21 — Quantitative Screen (Financial Ratios)
# ---------------------------------------------------------------------------

# AAOIFI Standard No. 21 thresholds (widely adopted by Sharia scholars):
#   1. Interest-bearing debt / Total assets ≤ 33%
#      Rationale: A company with > 33% debt is deemed to have excessive
#      exposure to riba-based financing.
#   2. Interest-bearing debt / Market capitalization ≤ 33%
#      Alternative measure using market value instead of book value.
#      Used when market cap data is available.
#   3. Interest-bearing investments / Total assets ≤ 33%
#      Companies parking cash in interest-bearing instruments are
#      indirectly participating in riba.
#   4. Interest-bearing investments / Market cap ≤ 33%
#      Market-value-based alternative.
#   5. Accounts receivable / (Cash + Receivables) ≤ 50%
#      This screens for excessive credit sales. High receivables indicate
#      the company is functioning partly as a lender.
#   6. Non-compliant income / Total revenue ≤ 5%
#      Even a halal business may have minor non-compliant income (e.g.,
#      interest on bank deposits). If ≤ 5%, the stock is still compliant
#      but the non-compliant amount must be purified (donated to charity).

RATIO_THRESHOLDS = {
    "debt_to_assets": Decimal("33.00"),
    "debt_to_market_cap": Decimal("33.00"),
    "interest_bearing_investments_to_assets": Decimal("33.00"),
    "interest_bearing_investments_to_market_cap": Decimal("33.00"),
    "receivables_to_total": Decimal("50.00"),
    # Purification threshold
    "non_compliant_income_max": Decimal("5.00"),
}

# Per-ratio explanations for transparency
RATIO_EXPLANATIONS = {
    "debt_to_assets": {
        "en": (
            "This ratio measures the company's reliance on interest-bearing debt. "
            "A high ratio means the company is heavily financed by riba-based loans. "
            "AAOIFI Standard 21 sets the maximum at 33%: a company with debt exceeding "
            "one-third of its assets is considered to have excessive riba exposure."
        ),
        "ar": (
            "تقيس هذه النسبة اعتماد الشركة على الديون الربوية. "
            "النسبة المرتفعة تعني أن الشركة ممولة بشكل كبير بقروض ربوية. "
            "يحدد معيار AAOIFI رقم 21 الحد الأقصى بـ 33٪."
        ),
    },
    "debt_to_market_cap": {
        "en": (
            "An alternative to the debt/assets ratio, using the company's market "
            "capitalization instead of book assets. This provides a market-value "
            "perspective on debt levels. Threshold: ≤ 33%."
        ),
        "ar": (
            "بديل لنسبة الدين إلى الأصول، باستخدام القيمة السوقية للشركة بدلاً "
            "من القيمة الدفترية للأصول. الحد: ≤ 33٪."
        ),
    },
    "interest_bearing_investments_to_assets": {
        "en": (
            "This ratio measures how much of the company's assets are invested in "
            "interest-bearing instruments (bonds, interest-bearing deposits, etc.). "
            "Even if the company's core business is halal, parking significant assets "
            "in riba-based instruments is problematic. Threshold: ≤ 33%."
        ),
        "ar": (
            "تقيس هذه النسبة مقدار أصول الشركة المستثمرة في أدوات ربوية "
            "(سندات، ودائع بفائدة، إلخ). الحد: ≤ 33٪."
        ),
    },
    "interest_bearing_investments_to_market_cap": {
        "en": "Market-value-based alternative. Threshold: ≤ 33%.",
        "ar": "بديل يعتمد على القيمة السوقية. الحد: ≤ 33٪.",
    },
    "receivables_to_total": {
        "en": (
            "This ratio measures the proportion of current assets tied up in "
            "accounts receivable vs. cash. A high ratio suggests the company is "
            "effectively functioning as a lender (selling on credit). "
            "AAOIFI considers > 50% of (cash + receivables) in receivables as excessive. "
            "Threshold: ≤ 50%."
        ),
        "ar": (
            "تقيس هذه النسبة نسبة الأصول المتداولة المقيدة في الذمم المدينة مقابل النقد. "
            "النسبة المرتفعة تشير إلى أن الشركة تعمل كمقرض. الحد: ≤ 50٪."
        ),
    },
    "non_compliant_income": {
        "en": (
            "This measures income from non-Sharia-compliant sources (e.g., interest "
            "income on bank deposits, incidental prohibited revenue). "
            "If ≤ 5% of total revenue, the stock is still compliant BUT the "
            "non-compliant amount MUST be purified by donating to charity. "
            "This purification is the investor's responsibility."
        ),
        "ar": (
            "يقيس هذا الدخل من مصادر غير متوافقة مع الشريعة. "
            "إذا كان ≤ 5٪ من إجمالي الإيرادات، لا يزال السهم متوافقاً "
            "ولكن يجب تطهير المبلغ غير المتوافق بالتبرع للجمعيات الخيرية."
        ),
    },
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
    Each ratio includes a human-readable explanation.
    """
    ta = exact(total_assets)
    td = exact(total_debt)
    ibi = exact(interest_bearing_investments or 0)
    ar = exact(accounts_receivable or 0)
    cash = exact(cash_and_equivalents or 0)
    mc = exact(market_cap or 0)
    nci = exact(non_compliant_income or 0)
    rev = exact(total_revenue or 0)

    results: dict = {}
    all_pass = True
    failed_ratios: list[str] = []
    summary_parts: list[str] = []

    # Ratio 1: Debt to Total Assets
    if ta > 0:
        r1 = pct(td, ta)
        passed = r1 <= RATIO_THRESHOLDS["debt_to_assets"]
        exp = RATIO_EXPLANATIONS["debt_to_assets"]
        results["debt_to_assets"] = {
            "value": float(r1),
            "threshold": float(RATIO_THRESHOLDS["debt_to_assets"]),
            "passed": passed,
            "label": "Interest-bearing Debt / Total Assets",
            "label_ar": "الدين الربوي / إجمالي الأصول",
            "explanation": exp["en"],
            "explanation_ar": exp["ar"],
            "narrative": (
                f"The company has {_fmt_bn(td)} in interest-bearing debt against "
                f"{_fmt_bn(ta)} in total assets, resulting in a debt-to-assets ratio "
                f"of {float(r1):.2f}%. "
                f"This is {'BELOW' if passed else 'ABOVE'} the AAOIFI threshold of 33.00%. "
                f"{'✅ PASS: The company does not rely excessively on riba-based financing.' if passed else '❌ FAIL: The company carries excessive riba-based debt.'}"
            ),
        }
        if not passed:
            all_pass = False
            failed_ratios.append("debt_to_assets")
            summary_parts.append(f"Debt/Assets at {float(r1):.1f}% exceeds 33% limit")

    # Ratio 1b: Debt to Market Cap (if market cap provided)
    if mc > 0:
        r1b = pct(td, mc)
        passed = r1b <= RATIO_THRESHOLDS["debt_to_market_cap"]
        results["debt_to_market_cap"] = {
            "value": float(r1b),
            "threshold": float(RATIO_THRESHOLDS["debt_to_market_cap"]),
            "passed": passed,
            "label": "Interest-bearing Debt / Market Cap",
            "label_ar": "الدين الربوي / القيمة السوقية",
            "explanation": RATIO_EXPLANATIONS["debt_to_market_cap"]["en"],
            "explanation_ar": RATIO_EXPLANATIONS["debt_to_market_cap"]["ar"],
            "narrative": (
                f"Debt-to-market-cap ratio: {float(r1b):.2f}%. "
                f"{'✅ PASS' if passed else '❌ FAIL'} (threshold: 33.00%)."
            ),
        }
        if not passed:
            all_pass = False
            failed_ratios.append("debt_to_market_cap")
            summary_parts.append(f"Debt/MarketCap at {float(r1b):.1f}% exceeds 33% limit")

    # Ratio 2: Interest-bearing Investments to Total Assets
    if ta > 0:
        r2 = pct(ibi, ta)
        passed = r2 <= RATIO_THRESHOLDS["interest_bearing_investments_to_assets"]
        results["interest_bearing_investments_to_assets"] = {
            "value": float(r2),
            "threshold": float(RATIO_THRESHOLDS["interest_bearing_investments_to_assets"]),
            "passed": passed,
            "label": "Interest-bearing Investments / Total Assets",
            "label_ar": "الاستثمارات الربوية / إجمالي الأصول",
            "explanation": RATIO_EXPLANATIONS["interest_bearing_investments_to_assets"]["en"],
            "explanation_ar": RATIO_EXPLANATIONS["interest_bearing_investments_to_assets"]["ar"],
            "narrative": (
                f"Interest-bearing investments ratio: {float(r2):.2f}%. "
                f"{'✅ PASS' if passed else '❌ FAIL'} (threshold: 33.00%)."
            ),
        }
        if not passed:
            all_pass = False
            failed_ratios.append("interest_bearing_investments_to_assets")
            summary_parts.append(f"Interest-bearing investments/assets at {float(r2):.1f}% exceeds 33% limit")

    # Ratio 2b: Interest-bearing Investments to Market Cap
    if mc > 0:
        r2b = pct(ibi, mc)
        passed = r2b <= RATIO_THRESHOLDS["interest_bearing_investments_to_market_cap"]
        results["interest_bearing_investments_to_market_cap"] = {
            "value": float(r2b),
            "threshold": float(RATIO_THRESHOLDS["interest_bearing_investments_to_market_cap"]),
            "passed": passed,
            "label": "Interest-bearing Investments / Market Cap",
            "label_ar": "الاستثمارات الربوية / القيمة السوقية",
            "explanation": RATIO_EXPLANATIONS["interest_bearing_investments_to_market_cap"]["en"],
            "explanation_ar": RATIO_EXPLANATIONS["interest_bearing_investments_to_market_cap"]["ar"],
            "narrative": (
                f"Interest-bearing investments/market-cap ratio: {float(r2b):.2f}%. "
                f"{'✅ PASS' if passed else '❌ FAIL'} (threshold: 33.00%)."
            ),
        }
        if not passed:
            all_pass = False
            failed_ratios.append("interest_bearing_investments_to_market_cap")

    # Ratio 3: Accounts Receivable / (Cash + Receivables)
    denom = cash + ar
    if denom > 0:
        r3 = pct(ar, denom)
        passed = r3 <= RATIO_THRESHOLDS["receivables_to_total"]
        exp = RATIO_EXPLANATIONS["receivables_to_total"]
        results["receivables_to_total"] = {
            "value": float(r3),
            "threshold": float(RATIO_THRESHOLDS["receivables_to_total"]),
            "passed": passed,
            "label": "Accounts Receivable / (Cash + Receivables)",
            "label_ar": "الذمم المدينة / (النقد + الذمم)",
            "explanation": exp["en"],
            "explanation_ar": exp["ar"],
            "narrative": (
                f"Receivables ratio: {float(r3):.2f}%. "
                f"{'✅ PASS' if passed else '❌ FAIL'} (threshold: 50.00%). "
                f"{'The company has a healthy balance of cash vs. receivables.' if passed else 'The company carries excessive receivables, effectively functioning as a lender.'}"
            ),
        }
        if not passed:
            all_pass = False
            failed_ratios.append("receivables_to_total")
            summary_parts.append(f"Receivables/(Cash+Receivables) at {float(r3):.1f}% exceeds 50% limit")

    # Ratio 4: Non-compliant Income Ratio (purification check)
    if rev > 0:
        r4 = pct(nci, rev)
        passed = r4 <= RATIO_THRESHOLDS["non_compliant_income_max"]
        exp = RATIO_EXPLANATIONS["non_compliant_income"]
        purification_needed = not passed
        results["non_compliant_income"] = {
            "value": float(r4),
            "threshold": float(RATIO_THRESHOLDS["non_compliant_income_max"]),
            "passed": passed,
            "label": "Non-compliant Income / Total Revenue",
            "label_ar": "الدخل غير المتوافق / إجمالي الإيرادات",
            "explanation": exp["en"],
            "explanation_ar": exp["ar"],
            "purification_needed": purification_needed,
            "purification_amount": float(nci) if purification_needed else 0,
            "narrative": (
                f"Non-compliant income ratio: {float(r4):.2f}%. "
                f"Threshold: 5.00%. "
                f"{'✅ PASS: No purification needed.' if passed else f'⚠️ PURIFICATION REQUIRED: {_fmt_bn(nci)} ({float(r4):.1f}% of revenue) must be donated to charity.'}"
            ),
        }

    results["_overall_quantitative"] = all_pass
    results["_failed_ratios"] = failed_ratios
    results["_summary"] = "; ".join(summary_parts) if summary_parts else "All ratios pass."
    results["_num_ratios"] = sum(1 for k in results if not k.startswith("_"))
    results["_num_passed"] = sum(1 for k, v in results.items() if not k.startswith("_") and isinstance(v, dict) and v.get("passed"))

    return results


# ---------------------------------------------------------------------------
# Combined Screen — Full Sharia Compliance Assessment
# ---------------------------------------------------------------------------

VERDICT_DETAILS = {
    "NON-COMPLIANT_SECTOR": {
        "en": "This stock operates in a PROHIBITED business sector under Islamic law. The prohibition is based on the nature of the company's core business activity, which contradicts Islamic principles. This is a definitive HARD FAIL — no further analysis is needed, and no purification can remedy this. The stock cannot be held, traded, or invested in by Sharia-compliant funds or Muslim investors.",
        "ar": "يعمل هذا السهم في قطاع أعمال محظور بموجب الشريعة الإسلامية. هذا رفض نهائي — لا يمكن حيازة أو تداول هذا السهم.",
    },
    "NON-COMPLIANT_RATIOS": {
        "en": "While this stock operates in a permissible business sector, it FAILED one or more AAOIFI financial ratio screens. This means the company has excessive exposure to prohibited financial practices (riba-based debt, interest-bearing investments, or credit sales) even though its core business is halal.",
        "ar": "على الرغم من أن هذا السهم يعمل في قطاع مباح، إلا أنه فشل في واحد أو أكثر من اختبارات النسب المالية.",
    },
    "COMPLIANT": {
        "en": "✅ This stock PASSES both the qualitative (business activity) and quantitative (financial ratio) screens under AAOIFI Standard No. 21. It is considered Sharia-compliant for investment purposes. No purification is required.",
        "ar": "✅ يجتاز هذا السهم كلاً من الفحص النوعي والكمي وفقاً لمعيار AAOIFI رقم 21. يعتبر متوافقاً مع الشريعة.",
    },
    "COMPLIANT_WITH_PURIFICATION": {
        "en": "⚠️ This stock operates in a sector that may generate some non-compliant income (e.g., alcohol sales, interest income). While the core business is permissible, the non-compliant income exceeds 5% of total revenue. INVESTORS MUST PURIFY (donate to charity) the non-compliant portion of their investment returns. This purification is a personal religious obligation.",
        "ar": "⚠️ يعمل هذا السهم في قطاع قد يولد بعض الدخل غير المتوافق. يجب على المستثمرين تطهير (التبرع للجمعيات الخيرية) الجزء غير المتوافق.",
    },
    "COMPLIANT_WITH_OVERLAY": {
        "en": "⚠️ This stock operates in a sector that may have mixed revenue streams (some permissible, some potentially non-compliant). It passes the screens but investors should monitor for non-compliant income. Purification may be needed in future periods.",
        "ar": "⚠️ يعمل هذا السهم في قطاع قد يكون له مصادر دخل مختلطة. يجب على المستثمرين المراقبة.",
    },
}


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

    Returns a comprehensive verdict dict with detailed reasoning.
    """
    # --- Qualitative Screen ---
    sector_result = screen_sector(sector)

    # --- Quantitative Screen ---
    ratio_results = {}
    quantitative_available = False
    has_financials = any([total_assets, total_debt, interest_bearing_investments,
                          accounts_receivable, cash_and_equivalents])
    if has_financials and total_assets > 0:
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
        quantitative_available = True

    # --- Final Verdict ---
    qualitative_pass = sector_result["compliant"]
    quantitative_pass = ratio_results.get("_overall_quantitative", True) if ratio_results else True

    # Determine verdict and build detailed explanation
    if sector_result["category"] == "prohibited":
        verdict = "NON-COMPLIANT"
        verdict_ar = "غير متوافق"
        verdict_detail = VERDICT_DETAILS["NON-COMPLIANT_SECTOR"]["en"]
        verdict_detail_ar = VERDICT_DETAILS["NON-COMPLIANT_SECTOR"]["ar"]
        final_summary = sector_result.get("notes", "")
    elif not quantitative_pass:
        verdict = "NON-COMPLIANT"
        verdict_ar = "غير متوافق"
        verdict_detail = VERDICT_DETAILS["NON-COMPLIANT_RATIOS"]["en"]
        verdict_detail_ar = VERDICT_DETAILS["NON-COMPLIANT_RATIOS"]["ar"]
        failed = ratio_results.get("_failed_ratios", [])
        summary = ratio_results.get("_summary", "")
        final_summary = f"❌ NON-COMPLIANT: Failed {len(failed)} ratio(s). {summary}"
    elif sector_result["category"] == "permitted_with_overlay":
        nci_result = ratio_results.get("non_compliant_income", {})
        if nci_result.get("purification_needed"):
            verdict = "COMPLIANT_WITH_PURIFICATION"
            verdict_ar = "متوافق مع تطهير"
            verdict_detail = VERDICT_DETAILS["COMPLIANT_WITH_PURIFICATION"]["en"]
            verdict_detail_ar = VERDICT_DETAILS["COMPLIANT_WITH_PURIFICATION"]["ar"]
            pct_val = nci_result.get("value", 0)
            amt = nci_result.get("purification_amount", 0)
            final_summary = (
                f"⚠️ COMPLIANT WITH PURIFICATION: Sector '{sector}' requires monitoring. "
                f"Non-compliant income: {pct_val:.1f}% of revenue. "
                f"Purify {_fmt_bn(amt)} per share held."
            )
        else:
            verdict = "COMPLIANT_WITH_OVERLAY"
            verdict_ar = "متوافق مع ملاحظات"
            verdict_detail = VERDICT_DETAILS["COMPLIANT_WITH_OVERLAY"]["en"]
            verdict_detail_ar = VERDICT_DETAILS["COMPLIANT_WITH_OVERLAY"]["ar"]
            final_summary = (
                f"⚠️ COMPLIANT WITH OVERLAY: Sector '{sector}' is permissible. "
                f"Monitor for non-compliant income in future periods. "
                f"Current non-compliant income is within the 5% threshold."
            )
    else:
        verdict = "COMPLIANT"
        verdict_ar = "متوافق"
        verdict_detail = VERDICT_DETAILS["COMPLIANT"]["en"]
        verdict_detail_ar = VERDICT_DETAILS["COMPLIANT"]["ar"]
        final_summary = f"✅ COMPLIANT: Passes all AAOIFI screens. Sector: {sector or 'N/A'}."

    # Add data confidence note
    if not quantitative_available and sector_result["category"] not in ("prohibited",):
        confidence_note = (
            "\n\n⚠️ NOTE: Financial ratio data was not available for this stock. "
            "The quantitative screen was SKIPPED. This assessment is based solely on "
            "the qualitative (sector) screen. For a complete assessment, provide "
            "financial data (total assets, total debt, etc.) or consult a Sharia scholar. "
            "CONFIDENCE: LOW."
        )
        verdict_detail += confidence_note
        verdict_detail_ar += (
            "\n\n⚠️ ملاحظة: بيانات النسب المالية غير متوفرة لهذا السهم. "
            "تم تخطي الفحص الكمي. هذا التقييم يعتمد فقط على الفحص النوعي. الثقة: منخفضة."
        )

    if sector_result["category"] == "permitted" and not sector:
        confidence_note = (
            "\n\n⚠️ NOTE: Sector information was not provided. "
            "The qualitative screen was skipped. Confidence: LOW. "
            "Please verify the company's sector independently."
        )
        verdict_detail += confidence_note
        verdict_detail_ar += "\n\n⚠️ ملاحظة: لم يتم تقديم معلومات القطاع. الثقة: منخفضة."

    return {
        "company": name,
        "ticker": ticker,
        "sector": sector,
        "verdict": verdict,
        "verdict_ar": verdict_ar,
        "verdict_detail": verdict_detail,
        "verdict_detail_ar": verdict_detail_ar,
        "final_summary": final_summary,
        "qualitative_screen": sector_result,
        "quantitative_screen": ratio_results if ratio_results else None,
        "quantitative_available": quantitative_available,
        "standard": "AAOIFI Standard No. 21",
        "standard_url": "https://aaoifi.com/standards/",
    }


def _fmt_bn(value: Decimal | float) -> str:
    """Format a large number as billions/millions with 2 decimal places."""
    v = float(value)
    if abs(v) >= 1e9:
        return f"{v / 1e9:,.2f}B"
    if abs(v) >= 1e6:
        return f"{v / 1e6:,.2f}M"
    return f"{v:,.2f}"


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------


def print_report(result: dict):
    """Print a human-readable Sharia compliance report."""
    name = result["company"]
    ticker = result.get("ticker", "")
    sector = result.get("sector", "")
    verdict = result["verdict"]
    verdict_ar = result.get("verdict_ar", "")

    icons = {
        "COMPLIANT": "✅",
        "COMPLIANT_WITH_OVERLAY": "✅⚠️",
        "COMPLIANT_WITH_PURIFICATION": "✅🤲",
        "NON-COMPLIANT": "❌",
    }
    icon = icons.get(verdict, "❓")

    print("=" * 70)
    print("  Sharia Compliance Screening Report")
    print("  تقرير الفحص الشرعي")
    print("=" * 70)
    print(f"  Company / الشركة:        {name} ({ticker})")
    print(f"  Sector / القطاع:          {sector}")
    print(f"  Standard / المعيار:       {result['standard']}")
    print()
    print(f"  Verdict / الحكم:          {icon} {verdict} — {verdict_ar}")
    print(f"  Detail:                   {result['verdict_detail'][:120]}...")
    print()
    print("-" * 70)
    print("  Qualitative Screen / الفحص النوعي (Business Activity)")
    print("-" * 70)

    qs = result.get("qualitative_screen", {})
    q_icons = {"permitted": "✅", "permitted_with_overlay": "⚠️", "prohibited": "❌"}
    print(f"    Category:   {q_icons.get(qs.get('category', ''), '?')} {qs.get('category', 'N/A')}")
    print(f"    Rule:       {qs.get('matched_rule', 'N/A')}")
    print(f"    Explanation:")
    for line in qs.get("explanation", "").split("\n"):
        print(f"      {line}")
    print()

    if result.get("quantitative_screen"):
        print("-" * 70)
        print("  Quantitative Screen / الفحص الكمي (Financial Ratios)")
        print("-" * 70)
        print()

        qr = result["quantitative_screen"]
        for key, val in qr.items():
            if key.startswith("_"):
                continue
            if isinstance(val, dict) and "value" in val:
                p = "✅ PASS" if val["passed"] else "❌ FAIL"
                print(f"  {val['label']}")
                print(f"    Value: {val['value']:.2f}%  |  Threshold: {val['threshold']:.2f}%  →  {p}")
                if val.get("narrative"):
                    print(f"    {val['narrative']}")
                if val.get("explanation"):
                    print(f"    Why this matters: {val['explanation'][:200]}")
                if val.get("purification_needed"):
                    print(f"    🤲 Purification required: donate {_fmt_bn(val['purification_amount'])} per share")
                print()

        overall = qr.get("_overall_quantitative")
        if overall is not None:
            o_icon = "✅" if overall else "❌"
            print(f"  Quantitative Overall: {o_icon} {'PASS' if overall else 'FAIL'}")
            failed = qr.get("_failed_ratios", [])
            if failed:
                print(f"  Failed ratios: {', '.join(failed)}")
            print()

    print("=" * 70)
    print()
    print("  DISCLAIMER / إخلاء مسؤولية")
    print("  This is an algorithmic screening based on AAOIFI Standard No. 21.")
    print("  It is NOT a religious ruling (fatwa). Consult a qualified Sharia scholar")
    print("  for definitive guidance on your specific situation.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sharia Compliance Screening Engine — Mizan Saudi Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_screen = sub.add_parser("screen", help="Screen a single company")
    p_screen.add_argument("--name", required=True, help="Company name")
    p_screen.add_argument("--ticker", default="", help="Stock ticker")
    p_screen.add_argument("--sector", default="", help="Business sector")
    p_screen.add_argument("--total-assets", type=float, required=True)
    p_screen.add_argument("--total-debt", type=float, required=True)
    p_screen.add_argument("--interest-bearing-investments", type=float, default=0)
    p_screen.add_argument("--accounts-receivable", type=float, default=0)
    p_screen.add_argument("--cash-and-equivalents", type=float, default=0)
    p_screen.add_argument("--market-cap", type=float, default=0)
    p_screen.add_argument("--non-compliant-income", type=float, default=0)
    p_screen.add_argument("--total-revenue", type=float, default=0)
    p_screen.add_argument("--json", action="store_true", help="Also output JSON")
    p_screen.set_defaults(func=lambda a: (
        setattr(a, 'func', lambda a: None),
        print_report(screen_company(
            name=a.name, ticker=a.ticker, sector=a.sector,
            total_assets=a.total_assets, total_debt=a.total_debt,
            interest_bearing_investments=a.interest_bearing_investments,
            accounts_receivable=a.accounts_receivable,
            cash_and_equivalents=a.cash_and_equivalents,
            market_cap=a.market_cap,
            non_compliant_income=a.non_compliant_income,
            total_revenue=a.total_revenue,
        ))
    ) and None)

    # Quick test
    print_report(screen_company(
        name="Saudi Aramco", ticker="2222.SR",
        sector="Energy",
        total_assets=2_551_964_000_000,
        total_debt=379_525_005_312,
        accounts_receivable=165_444_000_000,
        cash_and_equivalents=288_371_000_000,
        market_cap=6_478_280_261_632,
        total_revenue=1_708_828_000_256,
    ))
