# Auto-Founder AI — Architecture Reference

> **Version**: 1.0 | **Date**: May 2026
> Condensed visual reference. Full narrative in [`HLD.md`](./HLD.md) and [`lld/`](./lld/).

---

## 1. System Overview

```mermaid
flowchart TD
    subgraph Client["Client Layer"]
        FP["Founder Portal\nNext.js 14"]
        AD["Admin Dashboard"]
    end

    subgraph Edge["Edge & Gateway"]
        CF["CloudFront CDN"]
        ALB["ALB + WAF\nSSL Termination"]
        GW["NestJS API Gateway\nAuth · Rate Limit · Tenant Guard"]
        WS["Go WebSocket\nReal-time Log Streaming"]
    end

    subgraph Orchestration["Orchestration"]
        LG["LangGraph Orchestrator\nStateGraph · Fan-out · HITL"]
        KF["Kafka\nEvent Bus"]
    end

    subgraph AgentPods["Agent Worker Pods — EKS ap-south-1"]
        STR["1 Strategist\nIdea Validation"]
        ARC["2 Architect\nStack & Schema Design"]
        COD["3 Coder\nCode Generation"]
        REV["4 Reviewer\nTesting & Self-Healing"]
        DEV["5 DevOps\nInfra Deployment"]
        MKT["6 Marketer\nLaunch & GTM"]
        OPS["7 LLMOps\nGrowth & Learning"]
    end

    subgraph LLMs["LLM Routing Layer"]
        CL["Claude Sonnet\nComplex Reasoning"]
        G4["GPT-4o\nCode Gen · Copy"]
        G4M["GPT-4o-mini\nSimple CRUD"]
        DL["DALL-E 3\nVisuals"]
    end

    subgraph Data["Data Tier"]
        PG["PostgreSQL 16\nSchema-per-tenant"]
        RD["Redis Cluster\nSession · Cache"]
        QD["Qdrant\nVector Memory"]
        S3["AWS S3\nArtefacts · Reports"]
    end

    subgraph Sandbox["Sandbox"]
        DC["Docker + gVisor\nEgress Restricted"]
        ECR["AWS ECR\nContainer Images"]
    end

    FP & AD --> CF --> ALB
    ALB --> GW & WS
    GW --> LG
    LG --> KF
    LG --> STR --> ARC --> COD --> REV --> DEV --> MKT
    OPS -.->|"learns from all"| STR & ARC & COD & REV & DEV & MKT
    STR & ARC & COD & REV & DEV & MKT & OPS --> LLMs
    STR & ARC & COD & REV & DEV & MKT & OPS --> Data
    COD & REV --> DC --> ECR
    WS <--> RD

    style Client        fill:#f0f4ff,stroke:#4f46e5
    style Edge          fill:#faf5ff,stroke:#7c3aed
    style Orchestration fill:#fff7ed,stroke:#ea580c
    style AgentPods     fill:#f0fdf4,stroke:#16a34a
    style LLMs          fill:#fef2f2,stroke:#dc2626
    style Data          fill:#f0f9ff,stroke:#0284c7
    style Sandbox       fill:#fefce8,stroke:#ca8a04
```

---

## 2. Agent Pipeline

```mermaid
flowchart LR
    IDEA(["Founder Idea\ntext prompt"])

    IDEA --> STR["Strategist\nMarket Analysis\nLean Canvas\nViability Score\n< 30 min"]

    STR --> G1{{"HITL Gate 1\nViability\nBand?"}}
    G1 -->|"0–24 reject"| DEAD(["Notify Founder\nDo Not Proceed"])
    G1 -->|"25–100 proceed"| ARC["Architect\nOpenAPI Spec · ERD\nTech Stack · Cost\n< 45 min"]

    ARC --> G2{{"HITL Gate 2\nFounder\nApproval?"}}
    G2 -->|"rejected"| ARC
    G2 -->|"approved"| COD["Coder\nNext.js 14 · NestJS\nStripe · Auth0\n< 15 min"]

    COD --> REV["Reviewer\nLint · Tests · Security\nLLM-as-Judge\n< 20 min"]

    REV -->|"pass"| DEV["DevOps\nTerraform · EKS\nDNS · SSL · CI/CD\n< 10 min"]
    REV -->|"fail after 5 retries"| ESC(["Human\nEscalation"])

    DEV --> MKT["Marketer\nLanding Page · SEO\nProduct Hunt · Social\n< 2 hrs"]

    MKT --> G3{{"HITL Gate 3\nLaunch Control\nCenter"}}
    G3 -->|"rejected"| MKT
    G3 -->|"approved"| LIVE(["Live MVP +\nMarketing Live"])

    STR & ARC & COD & REV & DEV & MKT --> OPS["LLMOps\nFeedback Loops\nPrompt Optimization\nWeekly"]

    style G1   fill:#fef2f2,stroke:#dc2626
    style G2   fill:#fef2f2,stroke:#dc2626
    style G3   fill:#fefce8,stroke:#ca8a04
    style LIVE fill:#f0fdf4,stroke:#16a34a
    style DEAD fill:#fee2e2,stroke:#dc2626
    style ESC  fill:#fee2e2,stroke:#dc2626
```

---

## 3. Reviewer Self-Healing Loop

```mermaid
flowchart TD
    IN["GitHub PR\nfrom Coder Agent"]

    IN --> L["Lint\nESLint · Prettier · Ruff"]
    L -->|pass| U["Unit Tests\nJest · pytest"]
    L -->|fail| PL["LLM Patch\nAST-aware fix"] --> L

    U -->|pass| I["Integration Tests\nPlaywright · Docker Sandbox"]
    U -->|fail| PU["LLM Patch\nDiagnose + fix"] --> U

    I -->|pass| S["Security Scan\nTrivy · Semgrep · Bandit"]
    I -->|fail| PI["LLM Patch"] --> I

    S -->|pass| J["LLM-as-Judge\nReadability · Maintainability"]
    S -->|"HIGH/CRITICAL CVE"| PS["Security Patch"] --> S

    J -->|"score ≥ 75"| OK(["Approved\nEmit to DevOps"])
    J -->|"score < 75\n≤ 5 retries total"| PJ["Improve Code Quality"] --> J
    J -->|"5 retries exceeded"| HE(["Human Escalation"])

    RC["Retry Counter\nmax 5 across all loops"] -.-> PL & PU & PI & PS & PJ

    style OK fill:#f0fdf4,stroke:#16a34a
    style HE fill:#fef2f2,stroke:#dc2626
```

---

## 4. LLM Routing Policy

```mermaid
flowchart LR
    T["Incoming Task"] --> R["LLMOps Router\ncost-aware"]

    R -->|"Architecture · Self-healing\nSecurity review"| CL["Claude Sonnet\nComplex Reasoning"]
    R -->|"Code gen · Marketing\nStandard analysis"| G4["GPT-4o\nStandard Tasks"]
    R -->|"Simple CRUD · Boilerplate\nClassification · Formatting"| G4M["GPT-4o-mini\nSimple Tasks"]
    R -->|"Brand assets\nSocial visuals"| DL["DALL-E 3\nImage Generation"]

    CL & G4 & G4M --> CT["Cost Telemetry\nLLMOps Agent\nCOGS < ₹500/MVP"]

    style CL  fill:#fef2f2,stroke:#dc2626
    style G4  fill:#f0f4ff,stroke:#4f46e5
    style G4M fill:#f0fdf4,stroke:#16a34a
    style DL  fill:#faf5ff,stroke:#7c3aed
    style CT  fill:#fff7ed,stroke:#ea580c
```

---

## 5. Multi-Tenant Isolation

```mermaid
flowchart TD
    subgraph Platform["Auto-Founder AI Platform"]
        GW["API Gateway\nJWT → tenant_id extracted"]

        subgraph T1["Tenant A"]
            DB1["PostgreSQL\nschema: tenant_a"]
            S1["S3: tenant_a/..."]
            P1["Agent Pod\ntenant_a scope"]
        end

        subgraph T2["Tenant B"]
            DB2["PostgreSQL\nschema: tenant_b"]
            S2["S3: tenant_b/..."]
            P2["Agent Pod\ntenant_b scope"]
        end

        subgraph Shared["Shared (read-only infra)"]
            RD["Redis Cluster\nkeyed by tenant_id"]
            QD["Qdrant\ncollection per tenant"]
            KF["Kafka\npartitioned by tenant_id"]
        end
    end

    GW -->|"tenant_a JWT"| T1
    GW -->|"tenant_b JWT"| T2
    T1 & T2 --> Shared

    style T1     fill:#f0fdf4,stroke:#16a34a
    style T2     fill:#f0f4ff,stroke:#4f46e5
    style Shared fill:#f8fafc,stroke:#64748b
```

---

## 6. AWS Infrastructure

```mermaid
flowchart TD
    subgraph Internet["Internet"]
        USR["Founders / API Clients"]
    end

    subgraph AWS["AWS — ap-south-1"]
        subgraph Edge["Edge"]
            R53["Route53 DNS"]
            CF["CloudFront CDN"]
            WAF["AWS WAF"]
            ACM["ACM — TLS Certs"]
        end

        subgraph VPC["VPC  10.0.0.0/16"]
            subgraph Public["Public Subnets"]
                ALB["Application Load Balancer"]
                NAT["NAT Gateway"]
            end

            subgraph Private["Private Subnets"]
                subgraph EKS["EKS Cluster"]
                    CP["Control Plane"]
                    NG1["Node Group — API"]
                    NG2["Node Group — Agents"]
                    NG3["Node Group — Sandbox\ngVisor runtime"]
                end
                RDS["RDS PostgreSQL 16\nMulti-AZ"]
                EC["ElastiCache Redis\nCluster mode"]
            end
        end

        subgraph Storage["Storage & Messaging"]
            S3["S3 Buckets\ntenant-scoped"]
            MSK["Amazon MSK\nKafka"]
            ECR["ECR\nContainer Registry"]
            SM["Secrets Manager"]
        end

        subgraph Observability["Observability"]
            CW["CloudWatch\nLogs · Metrics · Alarms"]
            PROM["Prometheus + Grafana"]
            LS["LangSmith\nLLM Tracing"]
        end

        subgraph CD["GitOps CD"]
            ARGO["ArgoCD\nGitOps controller"]
        end
    end

    USR --> R53 --> CF --> WAF --> ALB
    ALB --> EKS
    EKS --> RDS & EC & S3 & MSK
    EKS --> SM
    ARGO --> EKS
    EKS --> CW & PROM & LS

    style Edge        fill:#faf5ff,stroke:#7c3aed
    style VPC         fill:#f0f9ff,stroke:#0284c7
    style EKS         fill:#f0fdf4,stroke:#16a34a
    style Storage     fill:#fff7ed,stroke:#ea580c
    style Observability fill:#fef2f2,stroke:#dc2626
    style CD          fill:#f0f4ff,stroke:#4f46e5
```

---

## 7. CI/CD Pipeline

```mermaid
flowchart LR
    DEV["Developer\nPush / PR"]

    DEV --> GHA["GitHub Actions"]

    subgraph CI["CI — on every PR"]
        L["Lint\nESLint · Black · Ruff"]
        T["Unit Tests\nJest · pytest"]
        SEC["Security Scan\nTrivy · Semgrep · Bandit"]
        EV["LLM Eval\nLangSmith judge"]
    end

    subgraph CD["CD — on merge to main"]
        BLD["Docker Build\nMulti-stage"]
        PUSH["Push to ECR"]
        SM["Staging Deploy\nArgoCD sync"]
        SMOK["Smoke Tests\nPlaywright"]
        PROD["Production Deploy\nArgoCD rolling update"]
    end

    GHA --> L --> T --> SEC --> EV
    EV -->|"all checks pass"| BLD --> PUSH --> SM --> SMOK --> PROD

    PROD --> LIVE(["Live on EKS\nautofoundeai.euron.one"])

    style CI   fill:#f0f4ff,stroke:#4f46e5
    style CD   fill:#f0fdf4,stroke:#16a34a
    style LIVE fill:#f0fdf4,stroke:#16a34a
```

---

*For detailed component specs, see [`HLD.md`](./HLD.md). For agent-level implementation, see [`lld/`](./lld/).*
