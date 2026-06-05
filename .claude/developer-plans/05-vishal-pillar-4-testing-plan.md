# Pillar 4 — Testing & Self-Healing: Technical Implementation Plan

> **Owner**: Vishal Prasad
> **Task ID**: AF-042 · **Branch**: `feature/reviewer-agent`
> **Status**: 🟡 Partially startable (lots of offline work)
> **Date**: 2026-06-04 · **Version**: 1.0.0
> **Depends on**: AF-036 (BaseAgent), AF-041 (Coder Agent repo output)
> **SLA**: < 15 minutes end-to-end · Sandbox spin-up < 10 s · Auto-fix rate ≥ 90% · Coverage ≥ 80%
> **Ground truth**: [reviewer-agent.md](../../docs/architecture/Agents-Architecture/reviewer-agent.md) (LLD) · root exemplar [testing-pillar-plan.md](../../testing-pillar-plan.md)

---

## Table of Contents

1. [Pillar Objective](#1-pillar-objective)
2. [Dependencies](#2-dependencies)
3. [Agent Architecture](#3-agent-architecture)
4. [Workflow Design](#4-workflow-design)
5. [Sub-Agent Recommendations](#5-sub-agent-recommendations)
6. [Tools & Integrations](#6-tools--integrations)
7. [Data Models](#7-data-models)
8. [Development Roadmap](#8-development-roadmap)
9. [Testing Strategy](#9-testing-strategy)
10. [Deliverables](#10-deliverables)

---

## 1. Pillar Objective

### 1.1 What Pillar 4 Achieves

Pillar 4 is the **quality-gate and self-healing engine** of the Auto-Founder AI pipeline. It receives a freshly generated code repository (Frontend + Backend) from the Coder Agent (Pillar 3) and autonomously runs a full quality-assurance pipeline — linting, unit + integration tests, end-to-end tests, security scanning, code-quality analysis, and an LLM-as-judge review — inside an **ephemeral, isolated Docker sandbox**. When failures are found, it enters a bounded **self-healing loop** (max 5 cycles): it triages each failure, generates minimal targeted patches, commits them, and re-runs the entire suite. Only code that passes every gate proceeds to deployment; anything it cannot fix is escalated to a human.

**Core mission**: Guarantee that every MVP leaving the factory is green, secure, and maintainable — turning AI-generated code (which is plausible but unverified) into production-grade, deployable software, with a written audit trail of what was tested, what was fixed, and what (if anything) still needs human eyes.

### 1.2 Specific Outputs Produced

| Output Category | Deliverable | Volume |
|---|---|---|
| **Verdict** | `review_decision` ∈ {`approved`, `escalate`} + `is_approved` boolean | 1 decision |
| **Test Suite Summary** | Lint results, unit + coverage, E2E, all rolled into the report | 5 result sets |
| **Security Audit** | Trivy (CVE + IaC) + Semgrep (SAST) + Bandit + Snyk + Gitleaks findings, OWASP-tagged | 1 findings list |
| **Quality Score** | SonarQube metrics + LLM-judge scores (readability / maintainability / security_posture / overall) | 1 score sheet |
| **Self-Heal Log** | Per-cycle patch history: issues targeted, patches applied, outcome | ≤ 5 cycles |
| **Patched Branch** | Commits pushed to the feature branch with the auto-fixes applied | 0–N commits |
| **Review Report** | Consolidated GitHub-flavoured Markdown report, posted as a PR comment + stored in S3 | 1 report |
| **gRPC Output** | `ReviewerOutput` protobuf → DevOps Agent (Pillar 5) | 1 message |

### 1.3 Inputs Received from Previous Pillars

| Source Pillar | Data Consumed | Required / Optional | Used For |
|---|---|---|---|
| **Pillar 3** — Code Generation (AF-041, Kartik) | `repo_url`, `pr_number`, `branch`, `coder_run_id` | **Required (critical)** | The repository to clone, build, test, patch, and report on |
| **Pillar 3** — Code Generation (AF-041) | Stack manifest (which languages / runners are present) | Required | Decides which linters / test runners / scanners to run |
| **Pillar 2** — Architecture (AF-040, Kaushlendra) | `FeatureList`, OpenAPI contract, ERD | Optional | LLM-judge can check the code implements contracted features |
| **Pillar 1** — Strategy (AF-037, Somesh) | `organization_id`, tenant tier | **Required** | Tenant scoping (UDAL), per-tier sandbox resource caps |
| **Pillar 7** — LLMOps (AF-045, Purnima) | Self-heal prompt tuning feedback (post-run) | Optional (feedback loop) | Improve triage/heal prompts |

### 1.4 Outputs Produced for Downstream Consumers

| Consumer | Data Emitted | Format |
|---|---|---|
| **DevOps Agent** (Pillar 5, AF-043 Prasenjit) | `ReviewerOutput` protobuf — decision, coverage, finding counts, report URI | gRPC / Protocol Buffers |
| **Founder Portal** (Frontend AF-057 Raunak) | Code Review Studio data: diff, comments, self-heal progress, scan table | JSON via REST + Realtime |
| **Mobile App** (AF-068 Yogesh) | Gate-approval preview on escalation | REST API |
| **UDAL** — Artifacts table | Review report + raw scan JSON | `tenant_uuid.artifacts` + S3 |
| **GitHub** | Review report PR comment; patch commits | GitHub REST API |
| **LLMOps Agent** (Pillar 7) | Heal-cycle telemetry, auto-fix rate | Kafka telemetry |

---

## 2. Dependencies

### 2.1 Mandatory Dependencies (Hard Blockers)

| Dependency | Task ID | Owner | Why It's Mandatory | Status |
|---|---|---|---|---|
| **BaseAgent ABC** | AF-036 | Asit / shared | `ReviewerAgent` subclasses it | 🔴 Blocked |
| **UDAL** | AF-027 | Somesh | All reads/writes via UDAL | ✅ Done |
| **FastAPI App Bootstrap** | AF-028 | Somesh | REST for Code Review Studio + escalation gate | ✅ Done |
| **Coder Agent output** | AF-041 | Kartik | The repo to test is the input | 🟡 Offline started |
| **Tool Registry (shell)** | AF-047 | Asit (shell) | Sandbox/scan/test tools registered | 🟡 |
| **LLM Router** | AF-049 | Purnima | Judge/triage/heal routing (Gemini 3.5 Flash) | 🟡 |
| **Docker daemon in sandbox host** | AF-013/infra | Asit / Prasenjit | Docker-in-Docker to build/run sandboxes | 🟡 Infra design |

### 2.2 Soft Dependencies (Optional but Beneficial)

| Dependency | Task ID | Owner | Fallback If Unavailable |
|---|---|---|---|
| Prompt Registry | AF-048 | Purnima | Load Jinja2 from filesystem |
| Guardrails Pipeline | AF-046 | Unassigned | Built-in OWASP hard-block + JSON-schema validators |
| Architect feature list | AF-040 | Kaushlendra | Skip "implements-features" judge check |
| SonarQube instance | AF-024 infra | Asit | Skip gate; `quality_gate_passed = false` |
| Redis | AF-032 | Asit | In-memory TTL dict for escalation pub/sub |
| Firecracker / gVisor | AF-043 infra | Prasenjit | Plain Docker + egress allow-list; harden Phase 2 |

### 2.3 Fallback Behavior Matrix

```
+----------------------------------+----------------------------------------------+
| Missing Input / Failure          | Fallback Strategy                            |
+----------------------------------+----------------------------------------------+
| repo_url / branch missing        | FATAL -- refuse to run; nothing to test;     |
|                                  | error_handler -> escalate                    |
+----------------------------------+----------------------------------------------+
| Dockerfile build fails           | FATAL for this run -- Coder must regenerate; |
|                                  | escalate with build log                      |
+----------------------------------+----------------------------------------------+
| Sandbox spin-up > 10s SLA        | Continue but log SLA breach; hard kill 30s   |
+----------------------------------+----------------------------------------------+
| Python-only / TS-only repo       | Skip the absent language's gates (SKIPPED,   |
|                                  | not FAILED)                                  |
+----------------------------------+----------------------------------------------+
| Semgrep cloud API down           | Fall back to local semgrep CLI               |
+----------------------------------+----------------------------------------------+
| SonarQube unavailable            | Skip gate; quality_gate_passed=false         |
+----------------------------------+----------------------------------------------+
| Snyk / Gitleaks unavailable      | Skip that scanner; non-fatal warning         |
+----------------------------------+----------------------------------------------+
| LLM invalid JSON (judge/triage)  | parse_with_correction re-prompts once;       |
|                                  | else retry node, then escalate               |
+----------------------------------+----------------------------------------------+
| Coverage < 80% after 5 cycles    | Escalate -- Coder must add tests             |
+----------------------------------+----------------------------------------------+
| OWASP CRITICAL/HIGH not fixable  | HARD BLOCK -- immediate escalate; never      |
|                                  | approve regardless of heal_cycle             |
+----------------------------------+----------------------------------------------+
| Heal cycles exhausted (=5)       | Escalate via Launch Control Center +         |
|                                  | PR comment + Slack alert                     |
+----------------------------------+----------------------------------------------+
```

### 2.4 Dependency Chain Visualization

```
Phase 1 -- DONE
   |
   v
Somesh --> AF-027 UDAL --> AF-028 FastAPI --> Asit AF-036 BaseAgent
                                                 |
                          +----------------------+----------------------+
                          v                      v                      v
              Kartik AF-041 Coder         Purnima AF-048/049      Asit AF-047
              (generated repo)            (Prompt Reg / Router)   (Tool Registry)
                    |                           |                      |
                    v                           v                      v
              +-------------------------------------------------------------+
              |   VISHAL -- AF-042 Reviewer / Self-Healer Agent             |
              |   Subclasses BaseAgent; reads repo via Coder output         |
              |   Prompt Registry for judge/triage/heal; LiteLLM routing    |
              |   Registers sandbox/scan/test tools                         |
              +-------------------------------------------------------------+
                    |
                    v
              AF-043 DevOps (Prasenjit, P5)  [approved repo]
              AF-057 Code Review Studio (Raunak)  [review data]
              AF-068 Mobile Gate (Yogesh)  [escalations]
```

---

## 3. Agent Architecture

### 3.1 Design Philosophy

A single `ReviewerAgent` LangGraph `StateGraph` with **13 nodes** + a central error sink. Shared mutable state (sandbox ID, accumulating results, heal history); five parallel test/scan nodes fan out against the same sandbox then converge at a barrier; the self-heal loop (`triage → auto_heal → spin_sandbox → tests → triage`) is a first-class graph cycle with a hard `MAX_HEAL_CYCLES = 5` guard; one report node produces one verdict.

### 3.2 ReviewerAgent Class

```python
# backend/app/agents/reviewer/agent.py
from app.agents.base import BaseAgent
from app.agents.reviewer.graph import build_reviewer_graph
from app.agents.reviewer.schema import ReviewerState

class ReviewerAgent(BaseAgent[ReviewerState, ReviewerState]):
    PILLAR = 4
    AGENT_ID = "reviewer"
    SLA_SECONDS = 900  # 15 minutes (excl. human escalation)

    async def understand(self, input_state): ...   # validate repo_url, pr_number, branch
    async def plan(self, intent): ...              # ingest, sandbox, parallel tests, judge, triage, heal, report
    async def execute(self, plan):
        graph = build_reviewer_graph(self.checkpointer)
        return await graph.ainvoke(self.state)
    async def verify(self, output): ...            # decision exists, coverage gate, no unresolved OWASP-critical
    async def learn(self, trace): ...              # heal-cycle telemetry to LLMOps
```

### 3.3 Internal Node Architecture

```
+----------------------------------------------------------------------------+
|                    ReviewerAgent (LangGraph StateGraph)                     |
|                                                                            |
|  +-------------+      +--------------+                                      |
|  | ingest_code |----->| spin_sandbox |<-------------------+                 |
|  +-------------+      +------+-------+                     | (heal loop:     |
|                             |                             |  patches applied)|
|         +-------------------+-------------------+         |                 |
|         v          v          v        v        v        |                 |
|  +-----------+ +---------+ +--------+ +-------+ +-------+  |                 |
|  |run_linters| |run_unit | |run_e2e | |run_sec| |run_   |  |                 |
|  |           | |_tests   | |_tests  | |_scan  | |sonar  |  |                 |
|  +-----+-----+ +----+----+ +---+----+ +---+---+ +---+---+  |                 |
|        +------------+----------+----------+---------+      |                 |
|                            v                              |                 |
|                     +------------+                        |                 |
|                     | test_join  |  (barrier -- waits 5)  |                 |
|                     +-----+------+                        |                 |
|                           v                               |                 |
|                     +-----------+                         |                 |
|                     | llm_judge |  (Gemini 3.5 Flash)     |                 |
|                     +-----+-----+                         |                 |
|                           v                               |                 |
|                  +-----------------+                      |                 |
|                  | triage_failures |  (Gemini 3.5 Flash)  |                 |
|                  +--------+--------+                       |                 |
|             approved|   heal|              escalate|       |                 |
|                     v       v                       v      |                 |
|          +----------------+ +-----------+   +-------------+ |                 |
|          |teardown_sandbox| | auto_heal |---+ error_handler||                 |
|          +-------+--------+ +-----------+    +------+------+|                 |
|                  v          (commit patches,       |       |                 |
|          +--------------+    heal_cycle++)          |       |                 |
|          | emit_report  |                           v       |                 |
|          +------+-------+                     (Slack + PR   |                 |
|                 v                              escalation)  |                 |
|              [END] --> DevOps Agent (Pillar 5)              |                 |
+----------------------------------------------------------------------------+
```

### 3.4 Node Responsibilities & I/O Contracts

| # | Node | Responsibility | Output | Model | SLA |
|---|---|---|---|---|---|
| 1 | `ingest_code` | Clone, parse, detect languages | `code_artifacts[]` | — | < 30 s |
| 2 | `spin_sandbox` | Build + run ephemeral container | `sandbox_container_id` | — | < 10 s |
| 3 | `run_linters` | ESLint/Prettier + Black/Ruff | `lint_results[]` | — | < 60 s |
| 4 | `run_unit_tests` | Jest + pytest + coverage ≥ 80% | `unit_test_result` | — | < 3 min |
| 5 | `run_e2e_tests` | Playwright | `e2e_test_result` | — | < 5 min |
| 6 | `run_security_scan` | Trivy + Semgrep + Bandit + Snyk + Gitleaks | `security_findings[]` | — | < 2 min |
| 7 | `run_sonarqube` | Quality gate | `sonarqube_metrics` | — | < 2 min |
| 8 | `test_join` | Barrier | merged state | — | — |
| 9 | `llm_judge` | Readability/maintainability/security scores | `llm_judge_score` | Gemini 3.5 Flash | < 1 min |
| 10 | `triage_failures` | Classify + route | `current_failures[]`, decision | Gemini 3.5 Flash | < 30 s |
| 11 | `auto_heal` | Generate + commit patches | `heal_history[+1]` | Gemini 3.5 Flash | < 3 min/cycle |
| 12 | `teardown_sandbox` | Cleanup | container removed | — | < 10 s |
| 13 | `emit_report` | Markdown report + PR comment + S3 | `review_report_markdown` | Gemini 3.5 Flash | < 1 min |
| E | `error_handler` | Force-teardown, escalate, Slack | `fatal_error` | — | — |

---

## 4. Workflow Design

### 4.1 End-to-End Workflow

```
Step 1: ORCHESTRATOR dispatches the testing step (inputs from Coder Agent)
Step 2: INGEST & VALIDATE -- clone + checkout; detect languages; FATAL if no artifacts
Step 3: SPIN SANDBOX (<10s) -- docker build + run (0.5 CPU, 512m, egress allow-list)
Step 4: PARALLEL TESTS (fan-out 5) -- linters || unit || e2e || security || sonarqube
        Language-absent branches mark SKIPPED, not FAILED
Step 5: TEST JOIN (barrier) -- verify lint + unit ran; merge results
Step 6: LLM-AS-JUDGE -- readability>=70 AND maintainability>=70 AND security_posture>=60
Step 7: TRIAGE -- classify auto_fixable / severity / OWASP; decision approved|heal|escalate
        OWASP CRITICAL/HIGH not-fixable -> escalate (hard block)
        coverage < 80% and cycles exhausted -> escalate
Step 8a: HEAL (decision==heal, cycle<5) -- patch SOURCE files only -> commit -> loop to sandbox
Step 8b: ESCALATE -- force teardown; PR comment; Slack + Redis pub; END
Step 9: APPROVED -- teardown_sandbox -> emit_report (PR comment + S3)
Step 10: EMIT -- store artifacts in UDAL; ReviewerOutput -> DevOps; pillar.completed{4};
         if heal_cycles_used >= 4 flag Coder-prompt review
```

### 4.2 Orchestration Sequence (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    participant Orch as Orchestrator
    participant Ing as ingest_code
    participant Sand as spin_sandbox
    participant Par as Parallel Test Nodes
    participant Join as test_join
    participant Jdg as llm_judge
    participant Tri as triage_failures
    participant Heal as auto_heal
    participant Rep as emit_report
    participant DevOps as DevOps Agent

    Orch->>Ing: ingest(repo_url, branch, pr_number)
    Ing-->>Orch: code_artifacts[]
    Orch->>Sand: spin_sandbox
    Sand-->>Orch: sandbox_container_id
    par Parallel
        Orch->>Par: linters / unit / e2e / security / sonarqube
    end
    Par-->>Join: results
    Join-->>Orch: merged
    Orch->>Jdg: judge
    Jdg-->>Orch: score (approved?)
    Orch->>Tri: triage
    Tri-->>Orch: failures + decision
    alt heal (cycle<5)
        Orch->>Heal: patch + commit -> loop to sandbox
    else approved
        Orch->>Rep: teardown + report -> ReviewerOutput
        Rep-->>DevOps: approved
    else escalate
        Orch->>Orch: error_handler -> PR + Slack
    end
```

### 4.3 Data Passed Between Nodes

```
ingest_code -> code_artifacts[]
   -> spin_sandbox -> sandbox_container_id
   -> [fan-out] lint_results / unit_test_result / e2e_test_result /
                security_findings / sonarqube_metrics
   -> test_join (barrier)
   -> llm_judge -> llm_judge_score(approved?)
   -> triage_failures -> current_failures[], review_decision
   -> auto_heal (if heal) -> heal_history[+1], heal_cycle++ -> loop to spin_sandbox
   -> teardown_sandbox (if approved)
   -> emit_report -> review_report_markdown, github_pr_comment_url, is_approved
   -> ReviewerOutput -> DevOps Agent (Pillar 5)
```

---

## 5. Sub-Agent Recommendations

### 5.1 Evaluation Matrix

| Proposed Sub-Agent | Recommendation | Rationale |
|---|---|---|
| Static Analysis | ✅ **Node** → `run_linters` | Deterministic subprocess |
| Unit Test Gen | 🔶 **Deferred / shared with Coder** | MVP runs tests; net-new test gen is Phase 2 (`generate_missing_tests`) |
| E2E Test | ✅ **Node** → `run_e2e_tests` | Playwright |
| Security Scanning | ✅ **Node** → `run_security_scan` | Trivy+Semgrep+Bandit+Snyk+Gitleaks; OWASP hard-block |
| Sandbox Manager | ✅ **Two nodes** → spin/teardown | Deterministic Docker calls |
| Code Quality | ✅ **Node** → `run_sonarqube` | Quality gate |
| LLM-as-Judge | ✅ **Node** → `llm_judge` | The reasoning gate |
| Triage | ✅ **Node** → `triage_failures` | Routes the loop |
| Self-Healer | ✅ **Node (loop entry)** → `auto_heal` | Checkpointed per cycle |
| AST-Aware Refactor | 🔶 **Phase 2** | Higher fidelity than snippet patches |
| Mutation Testing | 🔶 **Phase 3** | Validates test quality |
| DAST (OWASP ZAP) | 🔶 **Phase 2** | Needs running app + time budget |

### 5.2 Final Node Architecture

**Phase 1 (13 nodes):** ingest, spin_sandbox, 5 parallel gates, test_join, llm_judge, triage, auto_heal, teardown, emit_report.
**Phase 2:** `generate_missing_tests`, `ast_aware_heal`, `run_dast`.
**Phase 3:** `run_mutation_tests`, `run_load_tests`, `flaky_test_detector`.

---

## 6. Tools & Integrations

### 6.1 Per-Node Tool Registry

| Node | Tool | Service | Purpose | Env Variable |
|---|---|---|---|---|
| spin/teardown_sandbox | Docker SDK | local daemon | Build/run/remove container | `DOCKER_HOST` |
| run_linters/unit/e2e | exec_in_sandbox | container exec | Run tools in sandbox | — |
| run_security_scan | Trivy | local CLI | CVE + IaC scan | — |
| run_security_scan | Semgrep | semgrep.dev | SAST OWASP | `SEMGREP_APP_TOKEN` |
| run_security_scan | Bandit | container exec | Python security | — |
| run_security_scan | Snyk | api.snyk.io | Dep vulns | `SNYK_TOKEN` |
| run_security_scan | Gitleaks | local CLI | Secret detection | — |
| run_sonarqube | SonarQube REST | self-hosted | Quality gate | `SONARQUBE_URL`, `SONARQUBE_TOKEN` |
| auto_heal/emit_report | GitHub API | api.github.com | Commit patches + PR comment | `GITHUB_TOKEN` |
| emit_report | S3 | AWS S3 | Report + scan JSON | `AWS_S3_ARTIFACTS_BUCKET` |
| error_handler | Slack / Redis | Slack / ElastiCache | Escalation + LCC pub | `SLACK_WEBHOOK_REVIEWER`, `REDIS_URL` |

### 6.2 LLM Requirements

| Node | Model | Reason | Est. Tokens/Call |
|---|---|---|---|
| llm_judge | Gemini 3.5 Flash | Reasoning over code + results | ~6,000 in / ~600 out |
| triage_failures | Gemini 3.5 Flash | Classify + route | ~5,000 in / ~1,200 out |
| auto_heal | Gemini 3.5 Flash | Exact-snippet patches | ~6,000 in / ~3,000 out / cycle |
| emit_report | Gemini 3.5 Flash | Assemble Markdown | ~4,000 in / ~2,000 out |

**Worst case (5 cycles): ~66k in / ~27k out — well under < ₹500 COGS.**

### 6.3 External Service Rate Limits & Fallbacks

| Service | Limit | Timeout | Retry | Fallback |
|---|---|---|---|---|
| Docker build | 3/tenant | 30 s | fail fast | error_handler |
| Trivy | 10/min | 120 s | 3 | re-scan |
| Semgrep API | 60/hr | 120 s | 3 | local CLI |
| Snyk / Gitleaks | per-plan | 60/30 s | 3/1 | skip (non-fatal) |
| SonarQube | 20/min | 30 s | 3 | skip gate |
| Playwright | — | 300 s | 1 | skip E2E, add failure |
| GitHub API | 5,000/hr | 10 s | 3 (60 s) | continue (comment) / escalate (patch) |
| Gemini 3.5 Flash | 1,000 RPM | 30 s | 3 (45 s) | hard fail → escalate |

### 6.4 Database & Storage Requirements

| Store | Usage | Path / Key |
|---|---|---|
| PostgreSQL (UDAL) | run state, artifacts, gates | `tenant_uuid.artifacts` |
| pgvector | `code_patterns` (past fixes for heal RAG) | 768-dim HNSW |
| Redis | escalation pub/sub, build semaphore | `reviewer:escalate:{run_id}` |
| S3 | report + scan JSON + heal diffs | `s3://.../{org}/{run}/reviews/` |
| Docker (ephemeral) | sandbox images/containers | tag `reviewer-{run_id}-{cycle}` |

---

## 7. Data Models

```python
class ReviewDecision(StrEnum):
    APPROVED = "approved"; HEAL = "heal"; ESCALATE = "escalate"

MAX_HEAL_CYCLES = 5

class SecurityFinding(BaseModel):
    tool: str; severity: SeverityLevel; rule_id: str; file_path: str
    line: int | None = None; message: str
    owasp_category: OWASPCategory | None = None; cwe: str | None = None
    auto_fixable: bool = False; suppressed: bool = False

class TestSuiteResult(BaseModel):
    runner: str; total: int; passed: int; failed: int; skipped: int
    coverage_pct: float | None = Field(None, ge=0, le=100)
    failures: list[TestFailure] = []

class LLMJudgeScore(BaseModel):
    readability: int = Field(..., ge=0, le=100)
    maintainability: int = Field(..., ge=0, le=100)
    security_posture: int = Field(..., ge=0, le=100)
    overall: int = Field(..., ge=0, le=100); approved: bool = False

class ReviewerState(BaseModel):
    run_id: UUID; organization_id: str; coder_run_id: UUID
    repo_url: str; pr_number: int; branch: str
    code_artifacts: list = []; sandbox_container_id: str | None = None
    lint_results: list = []; unit_test_result: TestSuiteResult | None = None
    e2e_test_result: TestSuiteResult | None = None
    security_findings: list[SecurityFinding] = []
    sonarqube_metrics: dict | None = None
    llm_judge_score: LLMJudgeScore | None = None
    heal_cycle: int = 0; current_failures: list = []; heal_history: list = []
    review_decision: ReviewDecision | None = None
    is_approved: bool = False; fatal_error: str | None = None
```

(Full Pydantic V2 source in the [LLD](../../docs/architecture/Agents-Architecture/reviewer-agent.md) §2.)

---

## 8. Development Roadmap

### Phase 1 — MVP (Weeks 1–3)

| Week | Task | Deliverable | Status |
|---|---|---|---|
| 1 | **Sandbox runner prototype** (Docker build/run/exec/teardown) | `tools/sandbox.py` | 🟢 Start now |
| 1 | Schemas + 4 Jinja2 prompts (judge, triage, heal, report) | `schema.py`, `prompts/*.j2` | 🟢 Start now |
| 1 | 5 security-scan + 6 test/lint runner wrappers | `tools/*.py` | 🟢 Start now |
| 2 | StateGraph + 13 nodes + routers + self-heal loop | `graph.py`, `nodes/` | 🟡 Needs BaseAgent |
| 2 | Self-heal state machine + MAX_HEAL_CYCLES + OWASP hard-block | `nodes/auto_heal.py`, `utils/owasp.py` | 🟢 Start now |
| 3 | Wire ReviewerAgent to BaseAgent; 5 sample repos e2e | `agent.py` | 🔴 Needs AF-036 |

### Phase 2 (Weeks 4–6)
Real Trivy/Semgrep/Snyk/SonarQube; Firecracker/gVisor; real GitHub patches; AST-aware healing; `generate_missing_tests`; Code Review Studio contract (AF-057); SLA + Prometheus + PagerDuty.

### Phase 3 (Weeks 7–10)
DAST (OWASP ZAP); mutation testing; load tests; flaky-test detector; self-heal RAG over `code_patterns`.

---

## 9. Testing Strategy

### 9.1 Testing Without the Full Platform
Mock UDAL, `FakeLLM` (deterministic judge/triage/heal JSON), **real Docker** for the sandbox (least-blocked piece), HTTP mocks for Semgrep/Snyk/SonarQube + real Trivy/Bandit/Gitleaks CLIs, mock BaseAgent, LangGraph `MemorySaver`.

### 9.2 Test Architecture

```
tests/
├── unit/agents/reviewer/        # schema, routers, owasp, coverage-gate, heal-guard, parse, sla
├── integration/agents/reviewer/ # happy, heal, escalate(owasp/cycles/coverage), sonar-down, lang-skip, sandbox-fail
├── golden/reviewer/             # promptfoo.yaml + eval_{llm_judge,triage,auto_heal}.yaml
└── fixtures/sample_repos/       # clean, lint_errors, failing_unit_tests, sql_injection, low_coverage
```

### 9.3 Five Realistic Sample Repos (deterministic verdicts)

| Repo | Seeded defects | Expected verdict |
|---|---|---|
| `clean_nextjs_fastapi` | none | approved, 0 cycles, coverage 87% |
| `lint_errors` | 4 fixable ESLint errors | approved, 1 cycle |
| `failing_unit_tests` | 2 logic bugs + 1 lint warning | approved, 2 cycles (patch source, not tests) |
| `sql_injection` | OWASP A03 CRITICAL, not fixable | **escalate** (hard block, PagerDuty) |
| `low_coverage` | all pass but 62% coverage | **escalate** after 5 cycles |

### 9.4 Test Execution Commands

```bash
cd backend && uv run pytest tests/unit/agents/reviewer/ -v
cd backend && uv run pytest tests/integration/agents/reviewer/ -v   # needs Docker
cd backend && npx promptfoo eval --config tests/golden/reviewer/promptfoo.yaml
cd backend && uv run python -m app.agents.reviewer.e2e_test --repo fixtures/sample_repos/failing_unit_tests --mock-llm
```

### 9.5 Key Test Scenarios

| # | Scenario | Type | Pass Criteria |
|---|---|---|---|
| T1 | Happy path | Integration | approved; heal_cycle==0 |
| T2 | Lint auto-fix 1 cycle | Integration | heal_cycle==1; second pass green |
| T3 | Unit auto-fix 2 cycles | Integration | patches source not test files |
| T4 | OWASP CRITICAL not fixable | Integration | escalate; owasp_violations; PagerDuty |
| T5 | 5 cycles exhausted | Integration | escalate; reason mentions cycles |
| T6 | Coverage < 80% | Integration | escalate |
| T7 | SonarQube 503 | Integration | gate skipped; verdict still reached |
| T8 | Python-only repo | Integration | TS gates SKIPPED |
| T9 | Docker build fails | Integration | fatal; sandbox removed |
| T10 | Sandbox cleanup on error | Integration | no orphan containers |
| T11 | LLM invalid JSON | Unit | 1 self-correction |
| T12 | Node SLA breach | Unit | breach logged; pipeline continues |
| T13 | Concurrent tenant isolation | Integration | no cross-tenant leakage |
| T14 | High heal cycles (≥4 on approval) | Integration | `reviewer.high_heal_cycles` incremented |
| T15 | Coverage-gate validator (standalone) | Unit | < 80% → not approved |

---

## 10. Deliverables

### 10.1 File Structure

```
backend/app/agents/reviewer/
├── agent.py  graph.py  schema.py  routers.py
├── nodes/    (ingest_code, spin_sandbox, run_linters, run_unit_tests, run_e2e_tests,
│              run_security_scan, run_sonarqube, test_join, llm_judge, triage_failures,
│              auto_heal, teardown_sandbox, emit_report, error_handler)
├── tools/    (sandbox.py, eslint.py, python_lint.py, jest.py, pytest.py, playwright.py,
│              trivy.py, semgrep.py, bandit.py, snyk.py, gitleaks.py, sonarqube.py, github.py)
├── prompts/  (llm_judge.j2, triage_failures.j2, auto_heal.j2, emit_report.j2)
├── utils/    (retry.py, llm_parse.py, sla.py, owasp.py)
└── proto/    reviewer_output.proto
tests/        unit/ integration/ golden/ fixtures/sample_repos/
```

### 10.2 Environment Variables (`.env.example`)

```bash
# --- Reviewer Agent (Pillar 4) ----------------------------------------------
SEMGREP_APP_TOKEN=
SNYK_TOKEN=
SONARQUBE_URL=
SONARQUBE_TOKEN=
SLACK_WEBHOOK_REVIEWER=
# GITHUB_TOKEN, AWS_S3_ARTIFACTS_BUCKET, REDIS_URL, GEMINI_API_KEY already defined
```

### 10.3 Prompt Registry Entries (AF-048)

| Template | Version | Model | Variables |
|---|---|---|---|
| `reviewer/llm_judge` | 1.0.0 | Gemini 3.5 Flash | repo_url, branch, code_artifacts, unit_test_result, security_findings |
| `reviewer/triage_failures` | 1.0.0 | Gemini 3.5 Flash | heal_cycle, lint/unit/e2e/security/sonar/judge |
| `reviewer/auto_heal` | 1.0.0 | Gemini 3.5 Flash | current_failures, heal_history |
| `reviewer/emit_report` | 1.0.0 | Gemini 3.5 Flash | all state fields |

### 10.4 Tool Registry Entries (AF-047)

| Tool | Scope | Auth | Cost | Rate Limit |
|---|---|---|---|---|
| `spin_sandbox`/`teardown_sandbox` | Reviewer | Docker | Compute | 3 builds/tenant |
| `trivy_scanner` | Reviewer + DevOps | none | Free | 10/min |
| `semgrep_scanner` | Reviewer | API Key | Low | 60/hr |
| `snyk_scanner` | Reviewer | API Key | Medium | per-plan |
| `gitleaks_scanner` / `bandit_scanner` | Reviewer | none | Free | — |
| `sonarqube` | Reviewer | Token | Free | 20/min |
| `github_pr_comment`/`github_commit` | Reviewer + Engineering | OAuth | Free | 5,000/hr |

### 10.5 Prometheus Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `reviewer_node_duration_seconds` | Histogram | node, tenant, status | Per-node duration |
| `reviewer_heal_cycles_total` | Histogram | tenant, decision | Cycles used |
| `reviewer_autofix_rate` | Gauge | tenant | Fixed / fixable (≥ 90%) |
| `reviewer_security_findings_total` | Counter | severity, tool, owasp | Findings |
| `reviewer_owasp_blocks_total` | Counter | owasp | Hard-block escalations |
| `reviewer_decision_total` | Counter | decision | Verdict distribution |
| `reviewer_sla_breaches_total` | Counter | node | SLA breaches |
| `reviewer_high_heal_cycles_total` | Counter | tenant | Runs needing ≥ 4 cycles |

### 10.6 Kafka / EventBridge Events Emitted

| Event | Bus | Payload |
|---|---|---|
| `pillar.started{4}` | EventBridge | `{ run_id, coder_run_id }` |
| `pillar.completed{4}` | EventBridge | `{ run_id, review_decision, coverage_pct }` |
| `gate.required{human_review}` | EventBridge → SQS → UI | `{ run_id, escalation_reason, owasp_violations }` |
| `reviewer.security_critical` | EventBridge → PagerDuty | `{ run_id, owasp_violations }` |
| `reviewer.review_complete` | Kafka | `{ run_id, decision, heal_cycles_used, autofix_rate }` |
| `reviewer.high_heal_cycles` | Kafka | `{ run_id, coder_run_id }` (Coder-prompt review) |

### 10.7 gRPC Output Contract (ReviewerOutput protobuf)

```protobuf
syntax = "proto3";
package autofounder.reviewer.v1;
message ReviewerOutput {
  string run_id = 1; string organization_id = 2; string coder_run_id = 3;
  string repo_url = 4; string branch = 5; int32 pr_number = 6;
  string review_decision = 7; bool is_approved = 8;
  float unit_test_coverage = 9; int32 security_finding_count = 10;
  int32 critical_finding_count = 11; int32 llm_judge_overall = 12;
  int32 heal_cycles_used = 13;
  string review_report_url = 14; string github_pr_comment_url = 15;
  string escalation_reason = 16; repeated string owasp_violations = 17;
  int64 completed_at_unix_ms = 18; int32 total_llm_tokens_used = 19;
}
```

**Routing**: `approved` → DevOps (P5); `escalate` → Launch Control Center, block DevOps; OWASP CRITICAL → PagerDuty; `heal_cycles_used >= 4` → LLMOps reviews Coder prompts.

### 10.8 Immediate Action Items (🟢 Start Today)

| # | Task | Priority | Est. | Output |
|---|---|---|---|---|
| 1 | **Sandbox runner prototype** (zero platform deps, just Docker) | P0 | 6 hrs | `tools/sandbox.py` |
| 2 | Pydantic schemas | P0 | 4 hrs | `schema.py` |
| 3 | 5 security-scan wrappers | P0 | 5 hrs | `tools/*.py` |
| 4 | 6 lint/test runner wrappers | P0 | 5 hrs | `tools/*.py` |
| 5 | 4 Jinja2 prompts | P0 | 5 hrs | `prompts/*.j2` |
| 6 | Self-heal state machine + OWASP hard-block | P0 | 4 hrs | `nodes/auto_heal.py`, `utils/owasp.py` |
| 7 | Routers + retry + parse + SLA utils | P1 | 5 hrs | `routers.py`, `utils/` |
| 8 | 5 sample repos | P1 | 4 hrs | `fixtures/sample_repos/` |
| 9 | Unit tests + golden evals | P1 | 8 hrs | `tests/` |

**Total ~47 hrs. The sandbox runner (#1) is the single most valuable thing to build first — only piece with zero platform dependencies; every gate runs inside it.**

---

## Appendix A: Key Decisions Log

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D1 | One agent, 13 nodes | Single ReviewerAgent graph | Shared state; parallel gates; loop is a graph cycle |
| D2 | Heal loop bound | MAX_HEAL_CYCLES = 5 → escalate | Bounds cost; after 5 it's structural |
| D3 | Models | Gemini 3.5 Flash | Platform primary; cheap even at 5 cycles |
| D4 | OWASP critical | Hard block, never approve | Shipping SQL-injection is worse than a slow pipeline |
| D5 | Patch scope | SOURCE files only, never tests | Patching tests hides bugs |
| D6 | Coverage gate | < 80% → escalate (MVP) | Net-new test gen is Phase 2 |
| D7 | Sandbox isolation | Docker now → Firecracker/gVisor Phase 2 | Testable today, harden later |

## Appendix B: Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Sandbox escape | Low | Critical | Firecracker/gVisor + egress allow-list + ephemeral + non-root |
| Heal breaks working code | Medium | High | Minimal patches; re-run full suite; AST patching Phase 2 |
| Healer patches tests not source | Medium | High | Prompt rule + validator rejects patches to `*test*` |
| Judge false-approves | Medium | High | Objective gates decide independently; golden evals |
| OWASP mis-classified fixable | Low | Critical | Default CRITICAL/HIGH not-fixable; hard-block util |
| Loop never converges | Medium | Medium | heal_history anti-repeat + cycle cap |
| Orphan containers | Medium | Medium | teardown + error_handler force-removal; reaper by label |
| Coverage gate blocks good MVPs | Medium | Medium | Phase 2 `generate_missing_tests` |

## Appendix C: Coordination Checklist

| Who | What | When | Status |
|---|---|---|---|
| **Kartik (Pillar 3)** | Agree Coder→Reviewer contract: `repo_url`/`pr_number`/`branch`/`coder_run_id`/manifest | Immediately | ⬜ Pending |
| **Prasenjit (Pillar 5)** | Align Reviewer→DevOps `ReviewerOutput` handoff | Immediately | ⬜ Pending |
| **Asit (Platform)** | BaseAgent + UDAL + Docker-in-Docker on Fargate | When AF-036 starts | ⬜ Pending |
| **Asit (Platform)** | Register reviewer tools (AF-047) | When AF-047 shell exists | ⬜ Pending |
| **Purnima (Pillar 7)** | Register reviewer prompts (AF-048) + routing | When shells exist | ⬜ Pending |
| **Kaushlendra (Pillar 2)** | (Optional) FeatureList for judge feature-check | When convenient | ⬜ Pending |
| **Raunak (Frontend)** | Code Review Studio data contract (AF-057) | When mock data ready | ⬜ Pending |
| **Yogesh (Mobile)** | Mobile gate-approval preview (AF-068) | When mock data ready | ⬜ Pending |

---

*Auto-Founder AI — Pillar 4: Testing & Self-Healing Technical Plan v1.0.0 | June 2026*
*Owner: Vishal Prasad | Ground truth: docs/architecture/Agents-Architecture/reviewer-agent.md | Reviewed by: [Pending team review]*
