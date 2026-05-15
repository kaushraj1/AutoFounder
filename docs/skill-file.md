---
name: auto-founder-ai-agent-dev
description: >
  Use this skill whenever you are building, modifying, debugging, or extending any of the
  7 Auto-Founder AI agents (Strategist, Architect, Coder, Reviewer, DevOps, Marketer, LLMOps)
  or their associated tools, integrations, sandbox infrastructure, or LangGraph orchestration
  workflows. Also trigger when wiring new integrations (GitHub, Stripe, X, AWS, Tavily),
  writing Terraform/IaC, scaffolding new MVP code output templates, working on the
  multi-tenant NestJS API gateway, or implementing LLMOps pipelines. If the user mentions
  agents, pillars, LangGraph nodes, sandbox execution, self-healing loops, RLHF pipelines,
  or any Auto-Founder-specific feature — use this skill immediately.
---

# Auto-Founder AI — Agent Development Skill

## Core Principle: The 5-Stage Autonomous Loop
Every agent in Auto-Founder AI follows this pattern. When building or debugging any agent, verify all 5 stages are implemented:

1. **Understand** — Parse intent from idea, code, feedback, or signal (structured input validation)
2. **Plan** — Decompose into atomic, executable steps (LangGraph node graph)
3. **Execute** — Act via tools, APIs, sandboxes, integrations
4. **Verify** — Test outcome; self-correct on failure (up to N retries, configurable)
5. **Learn** — Feed result into RLHF + prompt-optimization pipeline (log to S3)

---

## Agent File Structure
Each agent lives at `src/agents/{agent-name}/`:

```
src/agents/strategist/
├── __init__.py
├── graph.py          # LangGraph StateGraph definition
├── nodes.py          # Individual node functions
├── state.py          # Pydantic v2 state schema
├── prompts.py        # System + user prompt templates
└── tools.py          # Agent-specific tool bindings (imports from src/tools/)
```

## State Schema Rules
- Always use **Pydantic v2** models for state — validate on entry and exit of every node
- Include `tenant_id: str` and `session_id: str` in every state schema (multi-tenancy requirement)
- Track `retry_count: int` and `max_retries: int` for self-healing loops
- Log `created_at`, `updated_at` timestamps on state for LLMOps tracing

```python
# Example state schema pattern
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AgentState(BaseModel):
    tenant_id: str
    session_id: str
    retry_count: int = 0
    max_retries: int = 5
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # ... domain-specific fields
```

---

## The 7 Agents — Implementation Reference

### 1. Strategist Agent (`src/agents/strategist/`)
**Pillar**: Idea Validation & Market Research
**Tools**: Tavily Search, RAG pipeline, Crunchbase, G2, Google Trends, SimilarWeb
**Key outputs**: Market Analysis Report (5-page), Lean Canvas (9 blocks), Viability Score, 3–5 ICPs
**Acceptance criteria**: Returns structured JSON with all Lean Canvas blocks + viability score 0–100
**Bias check**: Always run Western-centric bias audit before returning persona data

### 2. Architect Agent (`src/agents/architect/`)
**Pillar**: Architecture & Tech Stack Design
**Tools**: LLM (structured JSON output), Mermaid, OpenAPI/Swagger, AWS Pricing API, dbdiagram.io
**Key outputs**: ERD, OpenAPI spec, tech stack recommendation, cloud cost forecast (3 tiers)
**Gate**: Must present to founder for approval before Coder Agent starts — never auto-proceed

### 3. Coder Agent (`src/agents/coder/`)
**Pillar**: Autonomous Code Generation
**Tools**: LangGraph, AutoGen, GitHub API (Octokit), Docker, component libraries
**Key outputs**: Full Next.js 14 frontend + FastAPI/NestJS backend, Stripe integration, auth flows, Dockerfile
**Style enforcement**: Run ESLint + Prettier (TS) and Ruff + Black (Python) before handing to Reviewer
**Repo convention**: Always scaffold with proper CI/CD, `.env.example`, and README

### 4. Reviewer Agent (`src/agents/reviewer/`)
**Pillar**: Testing & Self-Healing
**Tools**: Jest, pytest, Playwright, Trivy, Semgrep, Bandit, Docker sandbox, AST parsers
**Self-healing loop**: lint → unit test → integration test → security scan → (if fail) → diagnose → patch → re-test (max 5 iterations)
**AST-aware patching**: Edit code at syntax-tree level, never regex replacement
**LLM-as-judge**: Second LLM scores readability/maintainability as final quality gate
**Pass criteria**: Zero linting errors + 100% core API route tests pass + no Trivy HIGH/CRITICAL findings

### 5. DevOps Agent (`src/agents/devops/`)
**Pillar**: Deployment & Infrastructure
**Tools**: Terraform, CloudFormation, ArgoCD, Helm, kubectl, Route53, Let's Encrypt, CloudWatch, Prometheus
**Key outputs**: Terraform IaC, Helm chart, GitHub Actions CI/CD config, DNS + SSL, Grafana dashboard
**Never**: Spend infra budget without HITL approval gate if cost > ₹10,000
**Rollback**: Always configure blue/green or canary deploy strategy

### 6. Marketer Agent (`src/agents/marketer/`)
**Pillar**: Marketing & Launch Automation
**Tools**: DALL-E 3 / Midjourney, Buffer, Typefully, ProductHunt API, X API, LinkedIn API, Resend, Ahrefs/Semrush
**Key outputs**: Brand kit, SEO landing page, 10 blog drafts, Product Hunt kit, HN "Show HN" post, X launch thread (8–10 tweets)
**Hallucination check**: Cross-reference all marketing copy against Architect Agent's actual feature list before output
**Rate limits**: Respect X/LinkedIn API rate limits — use Buffer/Typefully for scheduling, never post directly at volume
**B2B check**: If product is B2B, prioritize LinkedIn + niche subreddits over Product Hunt

### 7. LLMOps Agent (`src/agents/llmops/`)
**Pillar**: Growth, LLMOps & Continuous Learning
**Tools**: LangSmith, DSPy, Promptfoo, PostHog, Mixpanel, Prometheus, AWS Step Functions, S3
**Key functions**: Feedback capture, prompt optimization, model routing, drift detection, A/B testing, cost telemetry
**Model routing logic**: Route simple CRUD tasks → GPT-4o-mini; architecture/reasoning → Claude Sonnet; cost threshold triggers auto-downgrade
**Weekly pipeline**: Step Functions orchestrate RLHF data prep → prompt optimization → A/B test → promote winner

---

## Tool Development Pattern (`src/tools/`)
All tools must follow this signature for LangGraph compatibility:

```python
from langchain_core.tools import tool
from pydantic import BaseModel

class ToolInput(BaseModel):
    # always include tenant context
    tenant_id: str
    # ... tool-specific inputs

@tool
def tool_name(input: ToolInput) -> dict:
    """Clear docstring — this is used by the LLM for tool selection."""
    # implementation
    return {"status": "success", "data": ...}
```

---

## Integration Wrappers (`src/integrations/`)
Never call external SDKs directly from agent code. Always go through wrappers:

```
src/integrations/
├── github.py       # Octokit wrapper — PRs, commits, repo creation
├── aws.py          # Boto3 wrapper — EKS, S3, SQS, Secrets Manager
├── stripe.py       # Stripe wrapper — subscriptions, webhooks
├── tavily.py       # Tavily search wrapper
├── twitter.py      # X API wrapper with rate-limit handling
├── linkedin.py     # LinkedIn API wrapper
└── resend.py       # Email sending wrapper
```

---

## Sandbox Execution (`src/sandbox/`)
- Spin up ephemeral Docker containers for all code execution
- Strict egress network policy — no outbound except approved package registries
- Max lifetime: 30 minutes per sandbox, auto-destroyed after
- Spin-up target: < 10 seconds
- Use Firecracker or gVisor for additional isolation on untrusted code

```python
# Sandbox pattern
async def run_in_sandbox(code_path: str, tenant_id: str) -> SandboxResult:
    container = await sandbox_manager.spin_up(tenant_id=tenant_id)
    try:
        result = await container.execute(code_path)
        return result
    finally:
        await container.destroy()  # always destroy, even on exception
```

---

## LangSmith Tracing (Required on All Agents)
Every agent run must be traced:

```python
from langsmith import traceable

@traceable(name="strategist-market-research", tags=["pillar-1", "production"])
async def run_market_research(state: StrategistState) -> StrategistState:
    # implementation
```

---

## Multi-Tenant Safety Checklist
Before any data read/write operation, verify:
- [ ] `tenant_id` is present and validated in state
- [ ] Database query includes `WHERE tenant_id = :tenant_id`
- [ ] S3 path starts with `s3://auto-founder-ai/{tenant_id}/`
- [ ] No cross-tenant data leakage in logs or traces (mask sensitive fields)

---

## Common Pitfalls to Avoid
- **Never** use regex to patch generated code — always AST-aware manipulation
- **Never** pass raw user input directly to LLM — run prompt-injection detection first (`src/guardrails/`)
- **Never** hardcode API keys — use `src/integrations/secrets.py` → AWS Secrets Manager
- **Never** auto-proceed past HITL gates — these are non-negotiable for non-technical founders
- **Never** let the Marketer Agent promise features not confirmed in Architect Agent's output
- **Never** share tenant data in multi-tenant queries — always scope by `tenant_id`

---

## Testing Conventions
- Unit tests: `tests/unit/{agent-name}/`
- Integration tests: `tests/integration/` (require sandbox)
- LLM eval tests: `tests/evals/` (use LangSmith + Promptfoo)
- Security tests: run Trivy + Semgrep in CI on every PR via GitHub Actions
- Load tests: `tests/load/` — simulate Product Hunt spike (500 concurrent builds)
