# Governance & Compliance Spec — AutoFounder AI

> Extracted from `CLAUDE.md` §34, §35, §39 by `split_claude.py` (2026-06-04).
> `CLAUDE.md` is the lean index; this file holds the detail.
> Section numbers (`§N`) are preserved so cross-references stay valid.

---

## 34. Guardrails & Governance Layer

A **6-stage guardrails pipeline** wraps every agent invocation, plus a cross-cutting audit/lineage layer.

| # | Stage | Enforces | Tooling |
|---|---|---|---|
| 1 | **Policy & Rules** | Permission, usage, access control | OPA / Cedar |
| 2 | **Input Guardrails** | Content filters, PII redaction, injection detection | Llama Guard, Prompt Armor, Presidio |
| 3 | **Instruction Guardrails** | System prompts, constraints | Static prompt validators |
| 4 | **Execution Guardrails** | Safety checks, tool constraints, cost caps | Custom middleware on tool router |
| 5 | **Output Guardrails** | Hallucination check, quality, toxicity | TruLens, Llama Guard, citation-check |
| 6 | **Monitoring Guardrails** | Anomaly, drift, abuse detection | Evidently AI, PostHog, custom rules |
| ⌀ | **Audit & Lineage** | Traceability, logs, version history | Immutable audit log → S3 Object Lock |

Output Guardrail mandatory checks for the Marketing Agent: feature-claim cross-reference against Architect's feature list.

---

## 35. Compliance & Security Layer

- **Ethics & Responsible AI**: bias diversification in system prompts (anti-Western-centric, etc.); fairness audits.
- **Regulatory**: GDPR (right-to-erasure), CCPA, SOC 2 Type II, ISO 27001, HIPAA-ready, industry-specific.
- **Data Privacy & Protection**: encryption, masking, data minimization.
- **Interoperability & Explainability**: model cards (per registered model), decision lineage, data lineage.
- **Model Versioning & Registry**: model registry, experiment tracking (MLflow), rollback pointers.
- **Human-AI Collaboration**: explicit co-pilot mode, HITL escalation paths, feedback loops feeding RLHF.

---

## 39. Multi-Tenancy Rules

- **Database**: schema-per-tenant in PostgreSQL; never share schemas; RLS as defense-in-depth.
- **Vector store**: namespace per tenant.
- **Storage**: S3 paths prefixed `s3://{bucket}/{organization_id}/...`.
- **Compute**: agent worker tasks tenant-scoped; no shared in-memory state.
- **Auth**: every API call validates `organization_id` from JWT before any UDAL query.
- **Right to Erasure (GDPR)**: full tenant wipe across all stores (Postgres, vector, graph, S3, caches, audit excluded by law).

---
