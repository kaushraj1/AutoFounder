# Integrations Spec — AutoFounder AI

> Every third-party service we use, what it does for us, how we call it safely,
> and what we must never do with it.
>
> **Authoritative source**: `CLAUDE.md §15, §16, §31, §43`

---

## Integration Rules (apply to all services)

1. **Never call a third-party API directly from agent code.** All outbound calls go through the
   Tool Registry with schema validation and Execution Guardrail (Stage 4) applied first.
2. **All credentials** are stored in **AWS Secrets Manager** under `autofounder-ai/{env}/{service}/{key}`.
   Never in env vars committed to git, never in `docker-compose.yml` beyond `${VARIABLE}` references.
3. **Inbound webhooks** must validate the provider's HMAC signature before processing the payload.
4. **Circuit breakers** wrap every external call. On open: log `WARN`, return a typed error to
   the caller, do not retry immediately.
5. **Retry policy**: exponential backoff with ±20% jitter, max 3–5 attempts, capped at SLA budget.
6. **Cost attribution**: every API call that has a per-request cost records usage in `cost_ledger`
   with `organization_id`, `run_id`, `service`, `units`, `cost_usd`.

---

## Authentication — Supabase Auth

**Used for**: all human user authentication (OAuth 2.0 + SAML 2.0), organization management,
MFA enforcement, role assignment.

### JWT claims required

```json
{
  "sub":       "uuid",           // user ID (Supabase user)
  "organization_id": "uuid",           // tenant ID — mandatory on every call
  "role":      "founder",        // "founder" | "admin" | "super_admin"
  "scope":     "runs:read runs:write gates:decide"
}
```

### Rules

- MFA enforced via Supabase Auth for all human accounts. Cannot be disabled per-tenant.
- JWT validation uses `SUPABASE_JWT_SECRET` — verified on every request in the FastAPI auth middleware.
- Short-lived JWTs (15 min). Frontend refreshes silently via the Supabase Auth client.
- Machine-to-machine calls use API keys (hashed in `platform.organization_keys`).
- Refresh tokens rotate on every use.
- Service-to-service calls use mTLS + signed JWTs (SPIFFE-style identity).

### Environment variables (AWS Secrets Manager)

```
autofounder-ai/{env}/supabase/url
autofounder-ai/{env}/supabase/anon_key
autofounder-ai/{env}/supabase/service_role_key
autofounder-ai/{env}/supabase/jwt_secret
```

---

## Payments — Stripe

**Used for**: subscription billing (Solopreneur ₹10k/mo, Startup ₹50k/mo, Enterprise custom),
metered usage billing for token overages, checkout sessions.

### Integration points

| Event | AutoFounder AI action |
|-------|----------------------|
| `checkout.session.completed` | Activate tenant subscription, set tier |
| `invoice.paid` | Renew subscription, reset monthly build quota |
| `invoice.payment_failed` | Downgrade tenant to suspended, notify founder via email |
| `customer.subscription.deleted` | Suspend tenant, retain data for 30 days |

### Rules

- Webhook endpoint: `POST /v1/webhooks/stripe`
- Signature validation: `stripe.Webhook.construct_event(payload, sig_header, webhook_secret)`
- **Never** trust `amount` or `status` from the webhook body without re-fetching from Stripe API.
- Store Stripe `customer_id` and `subscription_id` in `platform.tenants`. Never store card data.
- Test with Stripe CLI: `stripe listen --forward-to localhost:8000/v1/webhooks/stripe`

### Environment variables (AWS Secrets Manager)

```
autofounder-ai/{env}/stripe/secret_key
autofounder-ai/{env}/stripe/webhook_secret
autofounder-ai/{env}/stripe/price_id_solopreneur
autofounder-ai/{env}/stripe/price_id_startup
```

---

## Transactional Email — Resend

**Used for**: HITL gate notifications, build completion alerts, welcome email on sign-up,
subscription receipts, launch confirmation.

### Rules

- All emails sent through `POST https://api.resend.com/emails`.
- Templates are versioned React Email components in `backend/app/emails/`.
- From address: `noreply@mail.autofounder.ai` (verified domain in Resend).
- Unsubscribe header required on all non-transactional emails.
- **Never** send email without founder opt-in. Transactional emails (gate alerts, receipts) are
  exempt from opt-in but must include an opt-out mechanism.

### Environment variables (AWS Secrets Manager)

```
autofounder-ai/{env}/resend/api_key
autofounder-ai/{env}/resend/from_address
```

---

## Push Notifications — SNS + Expo Push

**Used for**: mobile push notifications to the Expo app (HITL gate available, build completed,
run failed, launch approved).

### Flow

```
AutoFounder AI backend
  → Publish to Amazon SNS topic `push-notifications`
  → SQS queue (subscriber)
  → Notification worker (ECS task)
  → Expo Push API (api.expo.dev/v2/push/send)
  → Device (iOS APNs / Android FCM via Expo proxy)
```

The agent pipeline never calls the Expo Push API directly. It publishes to SNS.
The notification worker handles batching (up to 100 tokens per request), retries, and
token refresh.

### Rules

- Expo push tokens are stored per-user in `platform.user_devices` with `platform` (`ios` | `android`).
- Token refresh: Expo app sends new token on app launch via `POST /v1/devices/token`.
- Stale token (`DeviceNotRegistered` from Expo): delete from `platform.user_devices`.
- Notification payload must not contain PII — use `run_id` and `gate_id`, not idea text.
- Batch size: max 100 tokens per Expo Push API request.

### Environment variables (AWS Secrets Manager)

```
autofounder-ai/{env}/expo/access_token     (for Expo Push API auth)
autofounder-ai/{env}/aws/sns_push_topic_arn
```

---

## LLM Providers

AutoFounder AI routes to the **cheapest capable model** via LiteLLM. See `CLAUDE.md §31` for
the full routing table.

### Primary — Google Gemini (all task classes)

**Gemini 3.5 Flash** is the default model for all agent task classes:
- Complex reasoning, architecture, self-healing, LLM-as-judge
- Code generation (frontend + backend)
- Marketing copy, SEO content
- Classification, intent parsing, summarisation
- Vision (diagram extraction, screenshot QA)

**gemini-embedding-2** (768 dimensions) is the embedding model for all 7 vector collections.

```
autofounder-ai/{env}/gemini/api_key
```

### Image Generation

**DALL-E 3 / Midjourney / Stable Diffusion** — used by Marketing Agent for brand kits,
OG images, hero illustrations.

```
autofounder-ai/{env}/openai/api_key        (DALL-E 3)
autofounder-ai/{env}/midjourney/api_key
```

### Speech / Transcription

**OpenAI Whisper** — used by Input Layer for voice note transcription.

```
autofounder-ai/{env}/openai/api_key
```

### Safety Classifier

**Llama Guard 3** — Input Guardrail (Stage 2) classifies user-supplied text before it reaches
any LLM call site.

### Rules (all LLM providers)

- Token usage is recorded in `cost_ledger` after every call.
- All calls are traced to LangSmith with `run_id`, `agent_id`, `model`, `organization_id` tags.
- Per-tenant cost caps are checked before dispatching a call. If cap would be exceeded, the
  call is blocked and `AF_ERR_COST_CAP_EXCEEDED` is raised — not a silent drop.
- Prompt content containing user-supplied text has passed through Input Guardrail (Stage 2)
  before reaching the LLM call site.
- COGS target: < ₹500 per MVP build.

---

## Research & Market Intelligence

Called by the Research and Strategy agents via the Tool Registry.

| Service | Purpose | Rate limit (free tier) |
|---------|---------|----------------------|
| Tavily | Web search with AI-curated results | 1 000 req/month |
| SerpAPI | Google SERP results | 100 req/month |
| Crunchbase | Startup funding, competitor data | 200 req/month |
| G2 | SaaS product reviews | API key required |
| SimilarWeb | Traffic estimates | Limited free tier |
| Google Trends | Keyword trend data | Public API |
| ProductHunt | Product discovery | API key required |

```
autofounder-ai/{env}/tavily/api_key
autofounder-ai/{env}/serpapi/api_key
autofounder-ai/{env}/crunchbase/api_key
autofounder-ai/{env}/g2/api_key
autofounder-ai/{env}/similarweb/api_key
```

---

## Code & Repo — GitHub

**Used by**: Coder Agent (create repo, push branch, open PR), Reviewer Agent (push patches).

### Rules

- The GitHub App (not a personal token) authenticates all repo operations.
- Generated repos are created in the founder's connected GitHub account (OAuth scope: `repo`).
- The AutoFounder AI service account is added as a collaborator with `push` access for the
  build duration only. Removed when the run completes.
- Webhook on the generated repo listens for CI status to feed into Pillar 4 self-heal loop.

```
autofounder-ai/{env}/github/app_id
autofounder-ai/{env}/github/app_private_key
autofounder-ai/{env}/github/webhook_secret
```

---

## Marketing Platforms

Called by the Marketing Agent via the Tool Registry. **Nothing publishes publicly without
founder sign-off at the Launch Control Center HITL gate.**

| Service | Used for |
|---------|---------|
| X (Twitter) API v2 | Launch thread (8–10 tweets) |
| LinkedIn API | Cross-post + company page update |
| Reddit API | Relevant subreddit post |
| ProductHunt API | Product submission kit |
| Typefully | Thread scheduling |
| Mailchimp / Resend | Email drip sequences |

```
autofounder-ai/{env}/twitter/bearer_token
autofounder-ai/{env}/linkedin/access_token
autofounder-ai/{env}/producthunt/api_key
```

---

## Observability

| Service | Purpose |
|---------|---------|
| LangSmith | LLM call tracing, eval scores, prompt groundedness |
| Sentry | Frontend + backend error tracking |
| Prometheus + Grafana | Application-level RED + USE metrics |
| OpenTelemetry | Distributed tracing (W3C traceparent end-to-end) |
| AWS X-Ray | AWS-native trace aggregation (receives OTel spans) |

```
autofounder-ai/{env}/langsmith/api_key
autofounder-ai/{env}/sentry/dsn_backend
autofounder-ai/{env}/sentry/dsn_frontend
```

---

## Adding a New Integration

Checklist before any new third-party service goes into code:

- [ ] Credentials stored in **AWS Secrets Manager** under `autofounder-ai/{env}/{service}/`
- [ ] Tool definition added to Tool Registry (`tool_registry` table) with `args_schema`, `auth_scope`, `cost_class`, `rate_limit`
- [ ] Inbound webhook (if any) validates provider HMAC signature
- [ ] Circuit breaker configured with appropriate thresholds
- [ ] Usage recorded in `cost_ledger` if the service charges per call
- [ ] Added to `CLAUDE.md §43` integrations reference table
- [ ] Added to this spec document
