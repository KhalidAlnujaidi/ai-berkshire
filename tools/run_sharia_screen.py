#!/usr/bin/env python3
"""Run the Sharia screener on stocks.json with correct logic."""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from sharia_screener import screen_company, screen_sector, screen_ratios

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCKS_JSON = os.path.join(PROJECT, 'backend', 'stocks.json')

CONVENTIONAL_BANKS = {'1180', '1020', '1010'}
ISLAMIC_BANKS = {'1120', '1150', '2380', '1322'}
ALL_BANKS = CONVENTIONAL_BANKS | ISLAMIC_BANKS

with open(STOCKS_JSON) as f:
    stocks = json.load(f)

print('Sharia Compliance Screening (AAOIFI Standard No. 21)')
print('=' * 70)

compliant = 0
total = 0

for stock in stocks:
    if stock.get('market') != 'saudi':
        continue
    total += 1
    ticker = stock['ticker']
    name = stock.get('name_en', '?')

    sector = stock.get('sector_en', '')
    if ticker in CONVENTIONAL_BANKS:
        sector = 'Conventional Banking'

    is_bank = ticker in ALL_BANKS
    receivables_estimated = stock.get('_receivables_estimated', False)

    qual = screen_sector(sector)

    ar = stock.get('accounts_receivable', 0)
    if is_bank:
        ar = 0

    quant = screen_ratios(
        total_assets=stock.get('total_assets', 0),
        total_debt=stock.get('total_debt', 0),
        interest_bearing_investments=stock.get('interest_bearing_investments', 0),
        accounts_receivable=ar,
        cash_and_equivalents=stock.get('cash_and_equivalents', 0),
        market_cap=stock.get('market_cap', 0),
        non_compliant_income=stock.get('non_compliant_income', 0),
        total_revenue=stock.get('total_revenue', 0),
    )

    qual_pass = qual['compliant']
    quant_pass = quant.get('_overall_quantitative', True)

    if receivables_estimated and not is_bank:
        failed = {k for k, v in quant.items()
                  if isinstance(v, dict) and not v.get('passed', True)}
        real_fails = failed - {'receivables_to_total'}
        quant_pass = len(real_fails) == 0

    if not qual_pass:
        verdict = 'NON-COMPLIANT'
        reason = 'Prohibited sector: ' + sector
    elif not quant_pass:
        verdict = 'NON-COMPLIANT'
        failed_list = [k for k, v in quant.items()
                       if isinstance(v, dict) and not v.get('passed', True)]
        reason = 'Failed ratios: ' + ', '.join(failed_list)
    else:
        verdict = 'COMPLIANT'
        compliant += 1
        notes = []
        if receivables_estimated:
            notes.append('receivables estimated')
        if stock.get('data_quality') == 'partial':
            notes.append('partial data')
        reason = ' (' + '; '.join(notes) + ')' if notes else ''

    icon = '\u2705' if verdict == 'COMPLIANT' else '\U0001F6AB'
    print(f'  {icon} {ticker:6s} {name[:35]:35s} -> {verdict}{reason}')

print(f'\n  Halal stocks: {compliant}/{total}')
