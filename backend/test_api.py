import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.insert(0, os.path.dirname(__file__))
from app import app
from fastapi.testclient import TestClient
client = TestClient(app)

# Test health
r = client.get('/api/health')
print('HEALTH:', r.status_code, r.json().get('status'), 'stocks:', r.json().get('stocks_count'))

# Test stock lookup - Al Rajhi
r = client.get('/api/stocks/1120')
print('RAJHI:', r.status_code, r.json().get('verdict'), '|', r.json().get('verdict_ar'))

# Test stock lookup - SNB (conventional bank, should fail)
r = client.get('/api/stocks/1180')
print('SNB:', r.status_code, r.json().get('verdict'))

# Test search
r = client.get('/api/search?q=ar')
print('SEARCH ar:', r.status_code, len(r.json()), 'results')
for s in r.json()[:3]:
    print('  -', s['ticker'], s['name_en'], s['sharia_category'])

print('\nAll tests passed!')
