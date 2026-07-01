# Deployment Guide — Mizan (ميزان)

## Architecture

```
Internet ──▶ Cloudflare Tunnel ──▶ k3s Node (Traefik :80/:443)
                                        │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                    mizan-backend  mizan-frontend  mizan-postgres
                    (FastAPI:8000) (Next.js:3000)  (PG:5432)
```

All components run in a single-node **k3s** cluster. A **Cloudflare Tunnel**
(`cloudflared`) exposes the Traefik ingress to the internet over your custom
domain (`mizan-invest.com`), so no inbound ports need to be opened on the host.

Images are pushed from the host Docker daemon into an **in-cluster registry**
(NodePort `30500`) and imported into k3s containerd via the `image-importer` Job.

---

## Prerequisites on the host

```bash
# 1. k3s installed (includes Traefik, CoreDNS, containerd)
curl -sfL https://get.k3s.io | sh -

# 2. cert-manager (for TLS via Let's Encrypt — optional if using Cloudflare's edge TLS)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.1/cert-manager.yaml

# 3. kubectl points at the cluster
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

---

## 1. Create the namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

## 2. Create secrets

```bash
cp k8s/postgres-secret.example.yaml k8s/postgres-secret.yaml
# Edit postgres-secret.yaml — fill in JWT_SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL
kubectl apply -f k8s/postgres-secret.yaml
```

> `postgres-secret.yaml` is gitignored. **Never commit real secrets.**

## 3. Build & push images to the in-cluster registry

The registry runs as a NodePort service on port `30500`. From the host:

```bash
# Backend
docker build -t localhost:30500/mizan-backend:latest backend/
docker push localhost:30500/mizan-backend:latest

# Frontend
docker build -t localhost:30500/mizan-frontend:latest web/
docker push localhost:30500/mizan-frontend:latest
```

> If your host Docker talks to `localhost:30500` via HTTP (insecure registry),
> add `"insecure-registries": ["localhost:30500"]` to `/etc/docker/daemon.json`
> and restart Docker.

## 4. Import images into k3s

k3s uses containerd, not Docker. Import the freshly-pushed images:

```bash
kubectl apply -f k8s/registry.yaml
kubectl apply -f k8s/image-importer.yaml   # one-shot Job that pulls into containerd
# verify:
kubectl logs job/image-importer -n mizan
```

## 5. Deploy the stack

```bash
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/cluster-issuer.yaml   # Let's Encrypt ClusterIssuers
kubectl apply -f k8s/monitoring.yaml       # optional: Prometheus + ServiceMonitor
```

## 6. Set the frontend ConfigMap for production

The frontend reads `NEXT_PUBLIC_API_URL` from a ConfigMap. For production:

```bash
kubectl create configmap mizan-frontend-config \
  --from-literal=NEXT_PUBLIC_API_URL=https://mizan-invest.com/api \
  -n mizan \
  --dry-run=client -o yaml | kubectl apply -f -
```

## 7. Expose via Cloudflare Tunnel

### 7a. Create the tunnel (one-time)

```bash
cloudflared tunnel login
cloudflared tunnel create mizan          # writes credentials.json
cloudflared tunnel route dns mizan mizan-invest.com
cloudflared tunnel route dns mizan www.mizan-invest.com
```

### 7b. Configure & run

Place the generated `credentials.json` in `cloudflared/` (it is gitignored).

```bash
# From the repo root
./cloudflared/start-tunnel.sh
```

Or run it as a systemd service:

```bash
sudo cp cloudflared/mizan-tunnel.service /etc/systemd/system/
sudo systemctl enable --now mizan-tunnel
```

For an in-cluster cloudflared deployment instead, see
`k8s/cloudflared-config.yaml`.

---

## Verify the deployment

```bash
# Pods running?
kubectl get pods -n mizan

# Backend health
curl http://mizan.local/api/health          # from the host
curl https://mizan-invest.com/api/health    # from the internet

# Frontend
curl -I https://mizan-invest.com/

# TLS certificate issued?
kubectl get certificate -n mizan
```

---

## Post-Deploy Checklist

- [ ] Backend health check returns 200 at `/api/health`
- [ ] Frontend loads at `https://mizan-invest.com`
- [ ] CORS configured (`CORS_ORIGINS` references the prod URL)
- [ ] Sharia Checker returns results for sample tickers (1120, 2222, 7010)
- [ ] Frontend loads in both Arabic and English
- [ ] Cloudflare Tunnel is connected (`cloudflared tunnel info mizan`)
- [ ] TLS certificate is valid (no browser warnings)
- [ ] Prometheus can scrape `/metrics` (if monitoring enabled)

---

## Local Development (no K8s)

```bash
# Terminal 1: Backend
cd backend
python -m venv .venv && source .venv/bin/activate
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

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ImagePullBackOff` | Re-run `image-importer` Job after rebuilding images |
| 502/503 from Traefik | Pod not ready — check `kubectl describe pod -n mizan` |
| Cert stuck `Pending` | cert-manager not installed, or HTTP-01 challenge blocked |
| Tunnel shows `connection registered` but 502 | Traefik not binding host ports; check `kubectl get svc -A` |
| Frontend can't reach API | Wrong `NEXT_PUBLIC_API_URL` in ConfigMap; rebuild frontend image after changing |
