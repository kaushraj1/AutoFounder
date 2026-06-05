# Product & Roadmap Spec — AutoFounder AI

> Extracted from `CLAUDE.md` §3, §44, §45, §45b, §46, §47, §49 by `split_claude.py` (2026-06-04).
> `CLAUDE.md` is the lean index; this file holds the detail.
> Section numbers (`§N`) are preserved so cross-references stay valid.

---

## 3. Business Objective

Solve the four canonical founder failures:

| Failure | Cost in traditional path | AutoFounder AI |
|---|---|---|
| 90% of startups build things nobody wants | 3+ weeks, $5K+ on validation | 30 minutes |
| Wrong stack chosen | 1+ week debating | Architect Agent in minutes |
| MVP costs $15K–$50K and takes 3–6 months | 3–6 months | 7 days |
| Launch fizzles (zero traffic) | 2–3 extra weeks of GTM | 2 hours |
| **Total** | **4–7 months, $20K–$60K** | **~7 days, $200–$700** |

Targets: **99% faster, 99% cheaper, production-grade output**.

---

## 44. Pricing Tiers (for billing logic + generated copy)

| Tier | Price | Builds | Notes |
|---|---|---|---|
| AI Deep Researcher / Solopreneur | ₹10,000/mo | 1/month | Sandbox only |
| Startup Founder / Product Manager | ₹50,000/mo | 5/month | 1-click AWS/Azure deploy |
| Enterprise / Agency | Custom | Unlimited | Dedicated VPC, on-prem LLM, white-labeling |

**Revenue target**: ₹50 Lakhs MRR within 12 months.

---

## 45. Phases / What's In Scope Now

| Phase | Status | Scope | Milestone |
|---|---|---|---|
| Phase 1 — Validation Engine | **Active** | Strategy + Research + Product Planner agents; Lean Canvas; viability scoring | 10 pilot clients |
| Phase 2 — MVP Builder | Upcoming | Engineering agents (Architect → Coder → Reviewer); sandbox | 50 clients |
| Phase 3 — Launch & GTM | Planned | Marketing agent; social integrations; Launch Control Center | 150 clients |
| Phase 4 — Enterprise Scale | Planned | LLMOps CT pipelines; full AWS deploy automation; Finance & Ops/Risk agents | 300 clients |
| Phase 5 — Global Expansion | Planned | Multi-region, localization, marketplace | 1,000 clients |

### Phase 1 Sprint Plan

| Sprint | Weeks | Theme | Deliverables |
|---|---|---|---|
| Sprint 1 | 1–2 | "The Researcher Release" | Core Agents + Trace Logs |
| Sprint 2 | 3–4 | "The Founder Release" | One-click AWS + Managed UI |
| Sprint 3 | 5–6 | "The Agency Release" | Multi-tenancy + White-labeling |

**Out of scope (all phases)**: native mobile apps, hardware integrations, high-frequency trading, regulated medical software.

---

## 45b. Market Opportunity

| Segment | 2026 Value | 2030 Projection | CAGR |
|---|---|---|---|
| AI Coding Assistants | $2.1B | $12.5B | 24.5% |
| Low-Code / No-Code Platforms | $28B | $187B | 31.1% |
| Automated Marketing AI | $3.5B | $18.2B | 19.8% |

---

## 46. Open Questions / Assumptions

1. **AWS account ownership transfer** on eject — automation approach unresolved.
2. **Multi-cloud** (GCP / Azure) support — explicitly required by some AI Researcher cohorts; not yet designed. Reference architecture's S3/ADLS/GCS triad hints at it.
3. **Differentiation moat** as commoditization sets in — strategy pending.
4. **Pillar 8 (Mobile App Generation)** — Phase 2 scope, not designed.
5. **On-prem LLM** option for Enterprise tier — model registry supports it; ops playbook pending.
6. **Graph DB choice**: Neo4j vs Amazon Neptune — pending benchmark.
7. **Vector store**: **Resolved** — Supabase pgvector is the primary vector store (consolidates relational + vector into one platform).

---

## 47. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM hallucination in generated code or marketing | Output Guardrail + LLM-as-judge + feature-list cross-ref + ≥80% test coverage gate |
| Prompt injection via user idea text | Input Guardrail (Llama Guard + injection classifier + PII redaction) |
| Tenant data leakage | UDAL-enforced tenant scoping + schema-per-tenant + RLS + namespace-per-tenant vectors |
| Runaway LLM cost | Per-tenant cost caps, circuit breakers, cheapest-capable router, semantic cache |
| Deploy regression | Blue/green + smoke tests + 1-click rollback + canary ramp |
| Sandbox escape | Firecracker/gVisor isolation + strict egress allow-list + ephemeral lifetimes |
| Model drift | Drift Monitor (TruLens/Evidently) + weekly eval suite + rollback to last-good version |
| Vendor lock-in (single LLM) | Model registry + LiteLLM router + Bedrock multi-provider |
| Compliance breach | Audit & Lineage layer (immutable S3 Object Lock), quarterly pen-tests, AWS Config rules |
| Bias in market analysis | Bias Audit sub-workflow + diversified system prompts + human review on Strategy gate |

---

## 49. Future Enhancements

- **Pillar 8**: Mobile App Generation (React Native / Expo).
- **Pillar 9**: Compliance Automation (auto-generated SOC 2 evidence packs).
- **Multi-cloud agent runtime** (GCP Vertex / Azure AI Foundry) for AI Researcher tier.
- **On-prem LLM** packs for regulated Enterprise customers.
- **Marketplace** of community-contributed agents and templates plugged into the LangGraph orchestrator.
- **Synthetic data generation pipeline** (Layer 6 deliverable expansion).

> The blueprint's **Master Pattern** holds: every new pillar = new agents + new templates + new connectors **plugged into the existing LangGraph orchestrator**. The platform itself does not need to be rebuilt to scale horizontally across pillars.

---
