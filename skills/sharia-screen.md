# Sharia Compliance Screening — فحص التوافق الشرعي

Perform AAOIFI Standard No. 21 Sharia compliance screening on $ARGUMENTS.

**Supported input**: Company name, ticker, or sector. Examples:
- `/sharia-screen Al Rajhi Bank`
- `/sharia-screen 1120` (Tadawul ticker)
- `/sharia-screen "Saudi Aramco", "ACWA Power", "stc"`

---

## Why This Skill Exists

Value investing in Saudi Arabia requires an additional dimension beyond the four masters (Buffett, Munger, Duan Yongping, Li Lu): **Sharia compliance**. A company can pass every quality and valuation test and still be non-investable for the majority of Saudi investors if it fails the Sharia screen.

This skill answers two questions that no other AI Berkshire skill addresses:
1. **Is this stock halal?** (qualitative: what does the company do?)
2. **Does it pass financial ratio thresholds?** (quantitative: how leveraged is it?)

The answer is deterministic — calculated by `tools/sharia_screener.py`, not left to AI judgment.

---

## Execution Flow

### Step 1: Parse Input & Identify Companies

From $ARGUMENTS, identify all companies. For each:
- Company name, ticker, listing exchange (default: Tadawul)
- Business sector classification

### Step 2: Gather Financial Data (Parallel)

For each company, collect latest financial data (all in same currency):
1. **Balance sheet**: Total assets, total debt (interest-bearing), cash & equivalents
2. **Other**: Interest-bearing investments, accounts receivable
3. **Market data**: Market capitalization (if available)
4. **Revenue breakdown**: Non-compliant income (interest income, alcohol sales, gambling revenue, etc.)
5. **Sector classification**: Precise business activity description

### Step 3: Run Deterministic Screen

**MUST use the tool — do not calculate ratios by hand:**

```bash
python3 ~/ai-berkshire/tools/sharia_screener.py screen \
  --name "{company}" --ticker "{ticker}" --sector "{sector}" \
  --total-assets {value} --total-debt {value} \
  --interest-bearing-investments {value} \
  --accounts-receivable {value} --cash-and-equivalents {value} \
  --market-cap {value} \
  --non-compliant-income {value} --total-revenue {value}
```

For multiple companies, use batch mode:

```bash
python3 ~/ai-berkshire/tools/sharia_screener.py batch-screen companies.json
```

### Step 4: Interpret Results

The tool outputs one of four verdicts:

| Verdict | Arabic | Meaning | Action |
|---------|--------|---------|--------|
| ✅ **COMPLIANT** | متوافق | Passes all screens | Proceed with investment research |
| ✅⚠️ **COMPLIANT_WITH_OVERLAY** | متوافق مع ملاحظات | Permitted business, monitor income | Proceed; track non-compliant income quarterly |
| ✅🤲 **COMPLIANT_WITH_PURIFICATION** | متوافق مع تطهير | Permitted but needs charity donation | Proceed; calculate purification per share |
| ❌ **NON-COMPLIANT** | غير متوافق | Fails qualitative or quantitative screen | **Exclude from portfolio. Stop analysis.** |

### Step 5: Integration with Other Skills

- **If COMPLIANT**: Recommend running `/investment-research` or `/investment-checklist` for full analysis
- **If COMPLIANT_WITH_OVERLAY**: Flag for ongoing monitoring; recommend `/thesis-tracker` to track purification obligations
- **If NON-COMPLIANT**: Clearly state it is excluded from Sharia-compliant portfolios. Do NOT proceed to investment analysis. Suggest Sharia-compliant alternatives in the same sector if available.

### Step 6: Output Report

For each company, output:

1. **Sharia Verdict Banner** (bilingual EN/AR):
   ```
   ✅ COMPLIANT — متوافق
   Al Rajhi Bank (1120) — Banking
   ```

2. **Qualitative Screen Summary**:
   - Business activity assessment
   - Sector classification result
   - Any overlay requirements

3. **Quantitative Screen Table**:
   | Ratio | Value | Threshold | Result |
   |-------|-------|-----------|--------|
   | Debt / Total Assets | X.XX% | ≤33% | ✅/❌ |
   | Debt / Market Cap | X.XX% | ≤33% | ✅/❌ |
   | Interest Investments / Assets | X.XX% | ≤33% | ✅/❌ |
   | Receivables / (Cash+Receivables) | X.XX% | ≤50% | ✅/❌ |

4. **Purification Calculation** (if applicable):
   - Non-compliant income ratio
   - Purification amount per share

5. **Recommendation**: What skill to run next, or exclusion notice

### Step 7: Multi-Company Summary

When screening multiple companies, output a comparison table:

| Company | Sector | Verdict | Debt/Assets | Key Issue |
|---------|--------|---------|-------------|-----------|
| | | ✅/❌ | X% | |

Save report to: `reports/{company}-sharia-{YYYYMMDD}.md`

---

## Key Principles

- **Deterministic over subjective**: The tool calculates the verdict, not the AI. This prevents the "looks compliant" trap.
- **AAOIFI is the standard**: Use AAOIFI Standard No. 21 thresholds. These are the global consensus for Islamic finance screening.
- **Sharia compliance is a precondition, not a ranking**: A stock is either compliant or it isn't. There are no "degrees of halal."
- **Purification is a duty, not a penalty**: If a compliant company has minor non-compliant income, the purification is a charitable obligation, not a reason to avoid the stock.
- **Honesty with gray areas**: If sector classification is ambiguous, label it clearly and recommend consultation with a qualified Sharia scholar.
- **Data must be current**: Sharia compliance status can change. Always use the latest financial statements. Previous compliance does not guarantee future compliance.

## Reference: AAOIFI Standard No. 21 Thresholds

| Screen | Threshold | Source |
|--------|-----------|--------|
| Prohibited business activity | Any core involvement = FAIL | AAOIFI 21 §4 |
| Interest-bearing debt / Total assets | ≤ 33% | AAOIFI 21 §5-c-1 |
| Interest-bearing debt / Market cap | ≤ 33% | AAOIFI 21 §5-c-2 |
| Interest-bearing investments / Total assets | ≤ 33% | AAOIFI 21 §5-c-3 |
| Interest-bearing investments / Market cap | ≤ 33% | AAOIFI 21 §5-c-4 |
| Accounts receivable / (Cash + Receivables) | ≤ 50% | AAOIFI 21 §5-c-5 |
| Non-compliant income / Total revenue | ≤ 5% (purification if exceeded) | AAOIFI 21 §6 |

> *Note: Some Sharia scholars use slightly different thresholds. AAOIFI is the most widely adopted standard. Always disclose which standard is being applied.*
