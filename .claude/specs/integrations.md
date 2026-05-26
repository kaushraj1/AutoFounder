# Integrations Spec — AutoFounder AI

> Every third-party service we use, what it does for us, how we call it safely,
> and what we must never do with it.

---

## Integration Rules (apply to all services)

1. **Never call a third-party API directly from agent code.** All outbound calls go through the
   Tool Registry with schema validation and Execution Guardrail (Stage 4) applied first.
2. **All credentials** are stored in GCP Secret Manager. Never in env vars committed to git,
   never in `docker-compose.yml` beyond `${VARIABLE}` references.
3. **Inbound webhooks** must validate the provider's HMAC signature before processing the payload.
4. **Circuit breakers** wrap every external call. On open: log `WARN`, return a typed error to
   the caller, do not retry immediately.
5. **Retry policy**: exponential backoff with ±20% jitter, max 3–5 attempts, capped at SLA budget.
6. **Cost attribution**: every API call that has a per-request cost records usage in `cost_ledger`
   with `organization_id`, `run_id`, `service`, `units`, `cost_usd`.

---

## Payments — Stripe

**Used for**: subscription billing (Solopreneur ₹10k/mo, Startup ₹50k/mo, Enterprise custom),
metered usage billing for token overages, checkout sessions.

### Integration points

| Event | AutoFounder AI action |
|-------|----------------------|
| `checkout.session.completed` | Activate org subscription, set tier |
| `invoice.paid` | Renew subscription, reset monthly build quota |
| `invoice.payment_failed` | Downgrade org to suspended, notify founder via email |
| `customer.subscription.deleted` | Suspend org, retain data for 30 days |

### Rules

- Webhook endpoint: `POST /v1/webhooks/stripe`
- Signature validation: `stripe.Webhook.construct_event(payload, sig_header, webhook_secret)`
- **Never** trust `amount` or `status` from the webhook body without re-fetching from Stripe API.
- Store Stripe `customer_id` and `subscription_id` in `platform.organizations`. Never store card data.
- Test with Stripe CLI (`stripe listen --forward-to localhost:8000/v1/webhooks/stripe`).

### Environment variables (GCP Secret Manager paths)

```
autofounder-ai/{env}/stripe/secret_key
autofounder-ai/{env}/stripe/webhook_secret
autofounder-ai/{env}/stripe/price_id_solopreneur
autofounder-ai/{env}/stripe/price_id_startup
```

---

## Transactional Email — Resend

**Used for**: HITL gate notifications ("Your architecture is ready for review"), build completion
alerts, welcome email on sign-up, subscription receipts, launch confirmation.

### Rules

- All emails sent through `POST https://api.resend.com/emails`.
- Templates are versioned React Email components in `backend/src/autofounder-ai/emails/`.
- From address: `noreply@mail.autofounder.ai` (verified domain in Resend).
- Unsubscribe header required on all non-transactional emails.
- **Never** send email without founder opt-in. Transactional emails (gate alerts, receipts) are
  exempt from opt-in but must include an opt-out mechanism.

### Environment variables

```
autofounder-ai/{env}/resend/api_key
autofounder-ai/{env}/resend/from_address
```

---

## Push Notifications — Firebase Cloud Messaging (FCM)

**Used for**: mobile push notifications to the Expo app (HITL gate available, build completed,
run failed, launch approved).

### Flow

```
AutoFounder AI backend
  → Pub/Sub topic `push-notifications`
  → Cloud Function `send-fcm-notification`
  → FCM HTTP v1 API
  → Expo device
```

The backend never calls FCM directly. It publishes to Pub/Sub. The Cloud Function handles
batching, retries, and FCM token refresh.

### Rules

- FCM tokens are stored per-user in `platform.user_devices` with `platform` (`ios` | `android`).
- Token refresh: Expo app sends new token on app launch via `POST /v1/devices/token`.
- Stale token (FCM returns `UNREGISTERED`): delete from `platform.user_devices`.
- Notification payload must not contain PII — use `run_id` and `gate_id`, not idea text.

### Environment variables

```
autofounder-ai/{env}/fcm/service_account_json   (GCP Secret Manager, JSON blob)
autofounder-ai/{env}/pubsub/push_notifications_topic
```

---

## Authentication — Auth0

**Used for**: all human user authentication (OAuth 2.0 + SAML 2.0), organization management,
MFA enforcement, role assignment.

### JWT claims required

```json
{
  "sub":   "auth0|user_id",
  "org":   "org_01j...",           // organization_id
  "role":  "founder",              // "founder" | "admin" | "super_admin"
  "scope": "runs:read runs:write gates:decide"
}
```

### Rules

- MFA is enforced via Auth0 Actions for all human accounts. Cannot be disabled per-org.
- Machine-to-machine tokens use the Client Credentials flow with scoped API permissions.
- JWKS endpoint is fetched on startup and cached (re-fetched when a `kid` is unknown).
- Refresh tokens rotate on every use (Auth0 Rotating Refresh Token setting).

### Environment variables

```
autofounder-ai/{env}/auth0/domain
autofounder-ai/{env}/auth0/audience
autofounder-ai/{env}/auth0/client_id         (for M2M)
autofounder-ai/{env}/auth0/client_secret     (for M2M)
autofounder-ai/{env}/auth0/webhook_secret    (for management events)
```

---

## LLM Providers

AutoFounder AI routes to the **cheapest capable model** via LiteLLM. See `CLAUDE.md §31` for the
full routing table.

### Anthropic (Claude Sonnet)

**Used for**: complex reasoning, architecture decisions, self-healing, LLM-as-judge evaluation.

```
autofounder-ai/{env}/anthropic/api_key
```

### OpenAI (GPT-4o, GPT-4o-mini, Whisper, DALL-E 3, Embeddings)

**Used for**: standard code gen, marketing copy, classification, embeddings, speech transcription,
image generation for brand kits.

```
autofounder-ai/{env}/openai/api_key
autofounder-ai/{env}/openai/org_id
```

### Google Gemini (via Vertex AI)

**Used for**: GCP-native LLM calls (lower egress cost, no data leaving GCP region). Candidate to
replace OpenAI for code gen once eval results confirm quality parity.

```
# Authenticated via Workload Identity — no API key needed in Cloud Run
autofounder-ai/{env}/vertex/project_id
autofounder-ai/{env}/vertex/location
```

### Rules (all LLM providers)

- Token usage is recorded in `cost_ledger` after every call.
- All calls are traced to LangSmith with `run_id`, `agent_id`, `model`, `tenant_id` tags.
- Per-org cost caps are checked before dispatching a call. If cap would be exceeded, the call is
  blocked and a `AF_ERR_COST_CAP_EXCEEDED` error is raised (not a silent drop).
- Prompt content containing user-supplied text has passed through Input Guardrail (Stage 2)
  before reaching the LLM call site.

---

## Research & Market Intelligence

These tools are called by the Research and Strategy agents via the Tool Registry.

| Service | Purpose | Rate limit (free tier) |
|---------|---------|----------------------|
| Tavily | Web search with AI-curated results | 1 000 req/month |
| SerpAPI | Google SERP results | 100 req/month |
| Crunchbase | Startup funding, competitor data | 200 req/month |
| G2 | SaaS product reviews | API key required |
| SimilarWeb | Traffic estimates | Limited free tier |

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
- The AutoFounder AI service account is added as a collaborator with `push` access for the build
  duration only. It is removed when the run completes.
- Webhook on the generated repo listens for CI status to feed into Pillar 4 self-heal loop.

```
autofounder-ai/{env}/github/app_id
autofounder-ai/{env}/github/app_private_key
autofounder-ai/{env}/github/webhook_secret
```

---

## Observability

| Service | Purpose |
|---------|---------|
| LangSmith | LLM call tracing, eval scores, prompt groundedness |
| Sentry | Frontend + backend error tracking |
| Google Cloud Monitoring | GCP resource metrics, uptime checks |
| Prometheus + Grafana | Application-level RED + USE metrics |

```
autofounder-ai/{env}/langsmith/api_key
autofounder-ai/{env}/sentry/dsn_backend
autofounder-ai/{env}/sentry/dsn_frontend
```

---

## Adding a New Integration

Checklist before any new third-party service goes into code:

- [ ] Credentials stored in GCP Secret Manager under `autofounder-ai/{env}/{service}/`
- [ ] Tool definition added to Tool Registry (`tool_registry` table) with `args_schema`, `auth_scope`, `cost_class`, `rate_limit`
- [ ] Inbound webhook (if any) validates provider HMAC signature
- [ ] Circuit breaker configured with appropriate thresholds
- [ ] Usage recorded in `cost_ledger` if the service charges per call
- [ ] Added to this spec document
