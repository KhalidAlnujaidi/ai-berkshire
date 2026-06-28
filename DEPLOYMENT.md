# Deployment Guide — Mizan (ميزان)

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   Frontend (Vercel) │ ──API──▶│  Backend (Render)    │
│   Next.js 14        │         │  FastAPI + uvicorn   │
│   mizan-invest.com  │         │  api.mizan-invest.com│
└─────────────────────┘         └──────────────────────┘
```

## Backend Deployment (Render)

### Option A: Blueprint (recommended)

1. Push repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → New → Blueprint
3. Select this repo
4. Render reads `backend/render.yaml` automatically
5. Done — the API deploys at `https://mizan-api.onrender.com`

### Option B: Manual

1. Render Dashboard → New → Web Service
2. Connect GitHub repo
3. Settings:
   - **Runtime**: Python 3
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Health Check**: `/api/health`
4. Add environment variable `CORS_ORIGINS` with your Vercel URL

### Option C: Docker

```bash
cd backend
docker build -t mizan-api .
docker run -p 8000:8000 mizan-api
```

## Frontend Deployment (Vercel)

1. Go to [Vercel](https://vercel.com) → Import Project
2. Select the repo, set:
   - **Root Directory**: `web`
   - **Framework**: Next.js (auto-detected)
3. Set environment variable:
   - `NEXT_PUBLIC_API_URL` = your Render backend URL
4. Deploy — Vercel reads `web/vercel.json` automatically

## Post-Deploy Checklist

- [ ] Backend health check returns 200 at `/api/health`
- [ ] CORS configured (update `allow_origins` in `app.py` with your Vercel URL)
- [ ] Sharia Checker returns results for sample tickers (1120, 2222, 7010)
- [ ] Frontend loads in both Arabic and English
- [ ] Track Record section displays correctly

## Local Development

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
python app.py
# → http://localhost:8000

# Terminal 2: Frontend
cd web
npm install
cp .env.example .env.local
npm run dev
# → http://localhost:3000
```

## US Market Expansion

The Sharia screening engine (`tools/sharia_screener.py`) is **market-agnostic** — it applies AAOIFI ratios to whatever financial data you give it. To add US stocks:

1. Generate a template: `python3 tools/update_stocks_data.py template --ticker AAPL --market us`
2. Fill in financials from [SEC EDGAR](https://www.sec.gov/edgar/) or yfinance
3. Append to `backend/stocks.json`
4. The screener handles the rest automatically

The `market` field in stocks.json (`"saudi"` / `"us"` / `"hk"`) allows filtering by market in the API.
