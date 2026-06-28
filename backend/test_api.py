import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.insert(0, os.path.dirname(__file__))
from app import app
from fastapi.testclient import TestClient
client = TestClient(app)

# Test health
r = client.get('/api/health')
print('HEALTH:', r.status_code, r.json().get('status'), 'stocks:', r.json().get('stocks_count'))
assert r.status_code == 200
assert r.json()['stocks_count'] >= 49

# Test stock lookup - Al Rajhi (Islamic bank, should be compliant)
r = client.get('/api/stocks/1120')
print('RAJHI:', r.status_code, r.json().get('verdict'))
assert r.status_code == 200
assert 'COMPLIANT' in r.json()['verdict']

# Test stock lookup - SNB (conventional bank, should fail)
r = client.get('/api/stocks/1180')
print('SNB:', r.status_code, r.json().get('verdict'))
assert r.status_code == 200
assert r.json()['verdict'] == 'NON-COMPLIANT'

# Test search
r = client.get('/api/search?q=ar')
print('SEARCH "ar":', r.status_code, len(r.json()), 'results')
assert r.status_code == 200
assert len(r.json()) >= 1

# Test halal-stocks endpoint
r = client.get('/api/halal-stocks')
data = r.json()
print('HALAL STOCKS:', r.status_code, data['count'], 'halal of', data['total_screened'])
assert r.status_code == 200
assert data['count'] >= 1

# Test 404 for unknown ticker
r = client.get('/api/stocks/FAKE')
print('FAKE TICKER:', r.status_code)
assert r.status_code == 404

# Test custom screen
r = client.post('/api/sharia-screen', json={
    'name': 'Test Co', 'ticker': 'TEST', 'sector': 'Technology',
    'total_assets': 100_000_000, 'total_debt': 5_000_000,
    'cash_and_equivalents': 20_000_000, 'accounts_receivable': 10_000_000,
    'market_cap': 200_000_000, 'total_revenue': 50_000_000,
})
print('CUSTOM SCREEN:', r.status_code, r.json().get('verdict'))
assert r.status_code == 200

# Test portfolio screen - mixed portfolio
# Rajhi (compliant) + SNB (non-compliant)
r = client.post('/api/portfolio-screen', json={
    'holdings': [
        {'ticker': '1120', 'amount': 80000},
        {'ticker': '1180', 'amount': 20000},
    ]
})
print('\nPORTFOLIO SCREEN:', r.status_code)
assert r.status_code == 200
pdata = r.json()
summary = pdata['summary']
print(f'  Total: {summary["total_amount"]:,.0f} | Holdings: {summary["total_holdings"]}')
print(f'  Halal: {summary["halal_pct"]}% | NC: {summary["non_compliant_pct"]}% | Purif: {summary["purification_pct"]}%')
print(f'  Grade: {summary["grade"]} | {summary["grade_ar"]}')
assert summary['total_holdings'] == 2
assert summary['total_amount'] == 100000
assert summary['non_compliant_pct'] == 20.0
assert summary['halal_pct'] == 80.0
assert any(r['type'] == 'SELL' for r in pdata['recommendations'])
print(f'  Recommendations: {len(pdata["recommendations"])}')

# Test all-compliant portfolio (Rajhi only)
r = client.post('/api/portfolio-screen', json={
    'holdings': [
        {'ticker': '1120', 'amount': 100000},
    ]
})
assert r.status_code == 200
pdata = r.json()
print(f'\nALL-HALAL: grade={pdata["summary"]["grade"]}, halal={pdata["summary"]["halal_pct"]}%')
assert pdata['summary']['grade'] == 'SHARIA_COMPLIANT'
assert pdata['summary']['halal_pct'] == 100.0
assert any(r['type'] == 'GOOD' for r in pdata['recommendations'])

# Test with not-found ticker
r = client.post('/api/portfolio-screen', json={
    'holdings': [
        {'ticker': '1120', 'amount': 10000},
        {'ticker': 'FAKE', 'amount': 5000},
    ]
})
pdata = r.json()
print(f'\nWITH NOT-FOUND: holdings={pdata["summary"]["total_holdings"]}, not_found={pdata["not_found"]}')
assert 'FAKE' in pdata['not_found']
assert pdata['summary']['total_holdings'] == 1

print('\n\u2705 All tests passed!')
