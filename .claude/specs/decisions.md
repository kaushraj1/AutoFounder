# Architecture Decisions Spec — AutoFounder AI

> Extracted from `CLAUDE.md` §48 by `split_claude.py` (2026-06-04).
> `CLAUDE.md` is the lean index; this file holds the detail.
> Section numbers (`§N`) are preserved so cross-references stay valid.

---

## 48. Reconciliations vs Prior Document

The following architectural inconsistencies in the earlier `CLAUDE.md` are corrected here to match the blueprint:

| Topic | Prior `CLAUDE.md` | Corrected (this doc) |
|---|---|---|
| Compute platform | AWS EKS (Kubernetes), Helm, ArgoCD | **Amazon ECS on Fargate**, AWS CodeDeploy blue/green |
| Vector store | Qdrant → MongoDB Atlas | **Supabase pgvector** (consolidates relational DB + vector search into one platform) |
| Embedding model | `text-embedding-3-large` / `voyage-code-2` | **`gemini-embedding-2`** (aligns with Gemini primary LLM) |
| Message queue | Kafka (MSK, secondary) | **Confluent Kafka** (primary bus for all inter-agent events) |
| Object storage | S3 only | **Supabase Storage** (app tier) + S3 (data lake / audit, 7-yr retention) |
| LLM primary | Claude Sonnet / GPT-4o | **Gemini 3.5 Flash** |
| CI/CD | GitHub Actions + ArgoCD | **GitHub Actions** (primary); CodeDeploy retained for prod blue/green |
| COGS per MVP | $200–$700 (≈ ₹50K) | **< ₹500** (per README KPI) |
| Deployment infra (Pillar 5 README) | Noted as EKS in README pillar table | Kept as **ECS Fargate** — README pillar row is stale; §17 correction stands |
| API Gateway service | NestJS (Node 20) | **FastAPI (Python 3.12)** — all backend now Python |
| Realtime fan-out service | Go WebSocket service (`apps/realtime`) | **Supabase Realtime** (managed, no separate service) |
| Agent contract language | TypeScript | **Python** |
| ORM | Prisma | **SQLAlchemy + Supabase migrations** |
| Observability primary | ELK + Datadog + TruLens + Evidently | **Prometheus + Grafana** (per README); LangSmith for LLM tracing |
| Agent roster | 7 named agents (Strategist, Architect, Coder, Reviewer, DevOps, Marketer, LLMOps) | **7 specialized agents per blueprint** (Strategy & Ideation, Product Planner, Research, Engineering [composite], Marketing, Finance, Ops & Risk) + LLMOps as Layer-10 concern; sub-agents mapped explicitly |
| Layers | Implicit | **Explicit 10-layer reference architecture** |
| Memory | Redis + Qdrant | **6-tier memory model** (working, session, episodic, semantic, procedural, relational/graph, cold archive) |
| Graph DB | Missing | **Neo4j / Amazon Neptune** added |
| Feature store | Missing | **Feast / Tecton** added |
| Multi-modal input | Implicit text | **Explicit multi-modal Input Layer** (text/PDF/image/video/audio/streams/IoT/3rd-party) |
| Guardrails | Scattered | **Explicit 6-stage Guardrails & Governance Layer** + audit/lineage |
| Async bus | Kafka only | **EventBridge + SQS/SNS + Step Functions** (+ Kafka/MSK for high-throughput telemetry) |
| Unified data access | Missing | **UDAL** introduced — agents may not touch DBs directly |
| SLAs (MVP time) | "< 15 min" | **≤ 7 days** (per blueprint ROI table) |
| Pricing currency notes | INR only | INR maintained; COGS dual-noted as $200–$700 / < ₹50K |

---
