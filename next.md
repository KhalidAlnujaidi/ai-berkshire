# Mizan — next.md

> Working memory. Keep it short; injected into context.

## Done
- ✅ Backend (FastAPI): 49 Saudi stocks, 14 halal, AAOIFI Standard No. 21
- ✅ Frontend (Next.js 14): Full Arabic/English i18n, RTL, 15+ pages
- ✅ Auth (JWT + bcrypt): register, login, /me, password hashing
- ✅ Database (SQLAlchemy): auto SQLite↔PostgreSQL, User + WatchlistItem models
- ✅ Watchlist: server-synced when authenticated, localStorage fallback
- ✅ Kubernetes (k3s): 5 pods across 4 nodes, ingress, PV, probes, rolling updates
- ✅ Phase 1: secrets extracted, .bak cleaned, .gitignore hardened

## Next Priorities
1. **TLS/HTTPS** — cert-manager + Let's Encrypt (or self-signed for local cluster)
2. **CI/CD** — GitHub Actions to auto-build + deploy on push
3. **Live stock data** — Saudi Tadawul API or Yahoo Finance integration
4. **Password reset** — email-based recovery flow (no way to recover accounts yet)
5. **US market expansion** — SEC EDGAR data feed

## Boundaries
- `k8s/postgres-secret.yaml` — gitignored, real secrets live here only
- `backend/stocks.json` — core data, don't overwrite without backup
- `web/src/i18n/{en,ar}.ts` — large files, edit carefully
