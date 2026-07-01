# Mizan API Contract — AI Research Engine

**The product pivots:** the AI Investment Research Engine is the core. One subscription, pure gold — or demos only. Sharia screening becomes a section within each report.

---

## Data Models (new)

### ResearchReport
| Field | Type | Notes |
|-------|------|-------|
| `id` | int PK | Auto-increment |
| `user_id` | FK → users | Nullable for sample reports |
| `ticker` | str | e.g. `RKLB`, `1120` |
| `company_name` | str | Resolved from Yahoo or stocks.json |
| `status` | str | `pending` → `running` → `completed` / `failed` |
| `report_markdown` | text | Full markdown report (nullable until completed) |
| `summary` | str | One-line summary for list views |
| `rating` | str | `STRONG_BUY` / `BUY` / `HOLD` / `AVOID` / `WATCH` |
| `is_sample` | bool | True for public demo reports |
| `created_at` | datetime | |
| `completed_at` | datetime | Nullable |

### User (add columns)
| Field | Type | Notes |
|-------|------|-------|
| `subscription_status` | str | `free` / `active` / `canceled` (default `free`) |
| `stripe_customer_id` | str | Nullable |
| `stripe_subscription_id` | str | Nullable |
| `subscription_period_end` | datetime | Nullable |
| `subscription_plan` | str | `monthly` / `yearly` / null |

---

## Endpoints

### 1. POST `/api/research`
Start a research report. **Requires active subscription.**

**Request:**
```json
{ "ticker": "RKLB" }
```

**Response (201):**
```json
{
  "job_id": 42,
  "ticker": "RKLB",
  "status": "pending"
}
```

**Errors:**
- `402` — Subscription required (free user)
- `409` — Report already exists for this ticker in last 24h (return existing)
- `429` — Rate limit (max 5 reports/day per user)

---

### 2. GET `/api/research/{job_id}`
Poll for research status and result. **Auth required (owner only).**

**Response (200):**
```json
{
  "id": 42,
  "ticker": "RKLB",
  "company_name": "Rocket Lab USA",
  "status": "completed",
  "rating": "WATCH",
  "summary": "Space infrastructure play with strong moat but extreme valuation",
  "report_markdown": "# Rocket Lab USA (RKLB) ...\n\n...",
  "created_at": "2026-06-24T10:00:00Z",
  "completed_at": "2026-06-24T10:01:30Z"
}
```

Statuses: `pending` → `running` → `completed` | `failed`

When `pending`/`running`: `report_markdown`, `rating`, `summary` are null.
When `failed`: `error` field present, `report_markdown` null.

---

### 3. GET `/api/research/history`
List the user's past reports. **Auth required.**

**Query params:** `?limit=20&offset=0`

**Response (200):**
```json
[
  {
    "id": 42,
    "ticker": "RKLB",
    "company_name": "Rocket Lab USA",
    "status": "completed",
    "rating": "WATCH",
    "summary": "Space infrastructure play...",
    "created_at": "2026-06-24T10:00:00Z",
    "completed_at": "2026-06-24T10:01:30Z"
  }
]
```

---

### 4. GET `/api/research/samples`
**Public. No auth required.** Returns full demo reports.

**Response (200):**
```json
[
  {
    "id": 1,
    "ticker": "RKLB",
    "company_name": "Rocket Lab USA",
    "rating": "WATCH",
    "summary": "Space infrastructure play with strong moat but extreme valuation",
    "report_markdown": "# Rocket Lab USA (RKLB) ...",
    "created_at": "2026-06-24T10:00:00Z",
    "is_sample": true
  }
]
```

---

### 5. GET `/api/billing/subscription`
Check subscription status. **Auth required.**

**Response (200):**
```json
{
  "status": "active",
  "plan": "monthly",
  "current_period_end": "2026-07-24T10:00:00Z",
  "is_subscribed": true
}
```

Free user:
```json
{
  "status": "free",
  "plan": null,
  "current_period_end": null,
  "is_subscribed": false
}
```

---

### 6. POST `/api/billing/create-checkout-session`
Start Stripe Checkout. **Auth required.**

**Request:**
```json
{ "plan": "monthly" }
```

**Response (200):**
```json
{ "url": "https://checkout.stripe.com/..." }
```

---

### 7. POST `/api/billing/create-portal-session`
Manage subscription (cancel, update). **Auth required.**

**Response (200):**
```json
{ "url": "https://billing.stripe.com/..." }
```

---

### 8. POST `/api/billing/webhook`
Stripe webhook receiver. **Stripe signature verified.**

Handles: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`

**Response (200):** `{ "received": true }`

---

## Research Engine Internals

### `research_engine.py`

```python
async def generate_research_report(ticker: str, report_id: int, db_session) -> None:
    """Background task that generates a full research report."""
```

**Pipeline:**
1. Fetch financial data from Yahoo Finance (reuse `stock_data.py`)
2. Build a comprehensive prompt using the 4-master methodology (8 steps)
3. Call Anthropic Claude API with the prompt
4. Parse the response for rating + summary
5. Store the markdown report in `ResearchReport.report_markdown`
6. Update status to `completed` (or `failed` on error)

**LLM:** Anthropic Claude (`claude-sonnet-4-5-20250514` or similar)
**Timeout:** 120 seconds per report
**Prompt:** Encodes the full Buffett-Munger-Duan-Li Lu methodology from the existing skill

---

## Auth & Subscription Guard

```python
def require_subscription(user: User = Depends(get_current_user)) -> User:
    """Raises 402 if user is not subscribed."""
    if user.subscription_status != "active":
        raise HTTPException(status_code=402, detail="Subscription required")
    return user
```

---

## Existing Endpoints (unchanged)

All current endpoints remain: `/api/stocks`, `/api/sharia-screen`, `/api/watchlist`, `/api/portfolio`, `/api/alerts`, `/api/auth/*`. Sharia screening stays as a feature within the platform.
