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
assert r.json()['stocks_count'] >= 49  # 20 Saudi + 29 US

# Test stock lookup - Al Rajhi (Islamic bank, should be compliant)
r = client.get('/api/stocks/1120')
print('RAJHI:', r.status_code, r.json().get('verdict'), '|', r.json().get('verdict_ar'))
assert r.status_code == 200
assert 'COMPLIANT' in r.json()['verdict']  # COMPLIANT, COMPLIANT-WITH-OVERLAY, etc.

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
for s in r.json()[:5]:
    print(f'  - {s["ticker"]} {s["name_en"]} — verdict={s["verdict"]} is_halal={s["is_halal"]}')

# Test halal-stocks endpoint (Discover feature)
r = client.get('/api/halal-stocks')
data = r.json()
print('HALAL STOCKS:', r.status_code, data['count'], 'halal of', data['total_screened'], 'screened')
assert r.status_code == 200
assert data['count'] >= 1

# Test 404 for unknown ticker
r = client.get('/api/stocks/FAKE')
print('FAKE TICKER:', r.status_code)
assert r.status_code == 404

# Test custom screen endpoint
r = client.post('/api/sharia-screen', json={
    'name': 'Test Company',
    'ticker': 'TEST',
    'sector': 'Technology',
    'total_assets': 100_000_000,
    'total_debt': 5_000_000,
    'cash_and_equivalents': 20_000_000,
    'accounts_receivable': 10_000_000,
    'market_cap': 200_000_000,
    'total_revenue': 50_000_000,
})
print('CUSTOM SCREEN:', r.status_code, r.json().get('verdict'))
assert r.status_code == 200

print('\n✅ All tests passed!')
