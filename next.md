# bank — next.md

> Working memory for this project. Keep it short; it is injected into context.

## Now
- Mizan SaaS is LIVE and shareable: https://mizan-invest.com (and www)
- All fixes applied via CLI locally; no code changes were needed

## What was fixed (2026-07-02)
Two root-cause issues in Cloudflare Tunnel routing, both fixed via CLI/API:
1. **Live `tunnel-config` ConfigMap** (cloudflared ns) was missing mizan-invest.com routes — patched to add them, pointing at traefik.kube-system.svc
2. **DNS CNAME mismatch** — mizan-invest.com + www CNAMEs pointed at the *dead* mizan tunnel (507648c3, 0 connectors). Repointed both via Cloudflare API to the *live* juthoor tunnel (375d4444, 4 connections) which now serves all routes. Restarted cloudflared deploy.

## Deployment topology
- **Tunnel `juthoor`** (375d4444, RUNNING, 4 connections) serves: juthoor.io, analytics.juthoor.io, mizan-invest.com, www.mizan-invest.com
- **Tunnel `mizan`** (507648c3) is DEAD/unused — created but never ran a connector. Can be deleted later.
- mizan-invest.com → cloudflared → traefik (kube-system) → mizan namespace ingress → frontend (Next.js :3000) + backend (FastAPI :8000 via /api prefix)
- Backend serves all routes under /api/* (auth, watchlist, portfolio, alerts). Docs at /docs.

## Verified working
- apex + www: HTTP 200 (redirects to /ar locale)
- /api/auth/register: HTTP 200 (tested, returns JWT)
- /api/auth/login: HTTP 422 (route works)
- /api/auth/me, /api/watchlist: HTTP 401 (auth enforced)

## Boundaries
- Don't touch: juthoor.io routing (separate app), umami analytics
- `.kinox_residual_data/` is scratch — safe to clean
- Backend /health returns 404 (no health route) — harmless, could add one later
