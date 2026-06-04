# Operations & Observability Spec — AutoFounder AI

> Extracted from `CLAUDE.md` §20, §21, §22, §23, §24, §25, §26, §36, §38 by `split_claude.py` (2026-06-04).
> `CLAUDE.md` is the lean index; this file holds the detail.
> Section numbers (`§N`) are preserved so cross-references stay valid.

---

## 20. Async Processing / Queues

- **Primary message bus**: **Confluent Kafka** — all inter-agent events, pillar completions, and LLMOps telemetry.
- **Event routing**: Amazon EventBridge (schema registry, cross-service routing).
- **Work queues**: SQS (per-pillar queues, DLQs configured).
- **Pub/sub**: SNS for fan-out (notifications, webhooks).
- **Long-running orchestration**: AWS Step Functions (e.g., the weekly LLMOps optimization cycle).
- **Retry/backoff**: exponential with jitter, capped at agent SLA; failed messages → DLQ → on-call alert.

---

## 21. Observability & Monitoring

- **Metrics**: Prometheus + Grafana (RED + USE method dashboards).
- **Logging**: CloudWatch + Fluent Bit (structured JSON, `trace_id`, `organization_id`, `run_id`, `agent_id`).
- **Tracing**: OpenTelemetry → LangSmith (LLM call spans).
- **Model monitoring**: LangSmith evals (quality, hallucination tracking).
- **Errors**: Sentry (frontend + backend).
- **Cost & FinOps**: AWS Cost Explorer + custom per-tenant attribution dashboard.

Mandatory tags on every emitted signal: `organization_id`, `pillar`, `agent_id`, `model`, `run_id`, `env`.

---

## 22. Logging & Tracing

### 22.1 Trace propagation

- W3C `traceparent` header end-to-end (Web → API → Orchestrator → Agent → LLM call → DB).
- LangSmith captures per-step LLM I/O; cross-referenced with X-Ray spans via shared `trace_id`.

### 22.2 Log levels

`DEBUG` (dev only) · `INFO` (default) · `WARN` (recoverable) · `ERROR` (page on-call) · `AUDIT` (compliance, immutable to S3 Object Lock).

---

## 23. Error Handling & Retry Strategy

| Failure | Strategy |
|---|---|
| Transient LLM error (429/5xx) | Exponential backoff, jitter, max 5 retries |
| Tool failure | Retry once; if still failing, re-plan via reflection |
| Test failure (Pillar 4) | Self-heal loop, max 5 cycles, then HITL escalate |
| Deploy failure (Pillar 5) | Auto-rollback (blue/green), alert founder |
| Quota / cost cap exceeded | Pause run, notify founder, queue for next window |
| Guardrail violation (output) | Reject output, ask agent to revise; 3 strikes → escalate |
| Tenant data isolation breach (UDAL refuses) | Hard fail, fire SEV-1, page security on-call |

Circuit breakers (Hystrix-style) on every external integration. All failures emit `agent.failed` events for LLMOps drift detection.

---

## 24. Scalability Considerations

- **Stateless services** behind ALB; scale via ECS Service Auto Scaling (target tracking on CPU/RPS/SQS depth).
- **Concurrent builds target**: 500 (per tenant tier caps).
- **Database**: Supabase read replicas, connection pooling (Supabase built-in / PgBouncer), partitioning per tenant.
- **Vector store**: sharded by tenant; index warm-up on cold reads.
- **Hot-path caching**: Redis for plan checkpoints, prompt cache, embedding cache.
- **Load test baseline**: simulate Product Hunt spike (sudden burst traffic) before any SLA is signed off.

---

## 25. Performance Targets (Non-Negotiable)

| Metric | Target |
|---|---|
| UI response time (P95) | < 100 ms |
| Sandbox spin-up | < 10 s |
| Idea → Validated | < 30 min |
| Code gen (Pillar 3) latency | < 15 min |
| End-to-end (idea → live) | ≤ 7 days |
| Deploy SLA | < 10 min |
| Self-heal auto-fix rate | ≥ 90% |
| First-run deploy success | ≥ 85% |
| Test coverage on generated code | ≥ 80% |
| Uptime | 99.9% |
| Concurrent builds | 500 |
| COGS per MVP | < ₹500 |
| CSAT | > 4.5 / 5 |
| Day-90 user retention | Primary KPI |

---

## 26. Configuration Management

- **Per-env config**: SSM Parameter Store (non-secret) + Secrets Manager (secret).
- **Feature flags**: Statsig / GrowthBook / LaunchDarkly (LLMOps Agent toggles A/B variants).
- **Prompt versions**: stored in `prompt_registry` table + S3, immutable, semver-tagged.
- **Model registry**: model id, provider, version, eval scores, cost/token, rollback pointer.
- **No hard-coded values**: enforced by `semgrep` rule.

---

## 36. Observability & MLOps Foundation (Layer 10 detail)

| Pillar | Stack |
|---|---|
| Metrics | **Prometheus + Grafana** (primary) |
| Logging | CloudWatch + Fluent Bit |
| Tracing | OpenTelemetry → LangSmith (LLM call spans) |
| Model Monitoring | LangSmith evals |
| CI/CD & Automation | **GitHub Actions** (primary) + AWS CodeDeploy (ECS blue/green for prod deploys) |
| Feature Store | Feast / Tecton |
| Cost & FinOps | AWS Cost Explorer + per-tenant attribution dashboard |
| Environment Mgmt | dev / staging / prod (parity enforced) |

Feature Store usage: Pillar 7 maintains user/tenant features (engagement, COGS, accept-rate) consumed by the Model Router and Experimentation Agent.

---

## 38. Cost Optimization

- Cheapest-capable-model routing (§31).
- Aggressive prompt + response caching (semantic cache for retrieved contexts).
- Spot Fargate where workload tolerates.
- Per-tenant cost caps with circuit breakers.
- Weekly FinOps review by LLMOps Agent; regressions auto-paged.
- Target COGS per MVP: **$200–$700** (≈ < ₹50K).

---
