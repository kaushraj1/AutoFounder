# AutoFounder AI - Comprehensive Guardrails Specification

## Document Overview

**Document Version**: 1.0  
**Date**: 2026-06-12  
**Status**: Draft  
**Owner**: Asit Piri (Lead) + Purnima (Co-owner for Output/Monitoring stages)  
**Related**: AF-046 Guardrails Pipeline Implementation  

## Executive Summary

This document defines the comprehensive 6-layer guardrails system for AutoFounder AI, a multi-tenant agentic AI SaaS platform. The guardrails system provides a safety membrane that wraps every agent invocation to ensure security, compliance, quality, and monitoring across all AI operations.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Policy Layer Guardrails](#policy-layer-guardrails)
3. [Input Layer Guardrails](#input-layer-guardrails)
4. [Instruction Layer Guardrails](#instruction-layer-guardrails)
5. [Execution Layer Guardrails](#execution-layer-guardrails)
6. [Output Layer Guardrails](#output-layer-guardrails)
7. [Monitoring Layer Guardrails](#monitoring-layer-guardrails)
8. [Implementation Status](#implementation-status)
9. [Configuration & Deployment](#configuration--deployment)
10. [Compliance & Audit](#compliance--audit)

## Architecture Overview

The AutoFounder AI guardrails system implements a 6-stage pipeline that wraps every agent invocation:

```
Policy → Input → Instruction → [LLM/Agent] → Execution → Output → Monitoring
```

### Core Principles

- **Fail-Closed Security**: Security stages block execution when threats are detected
- **Fail-Open Quality**: Quality stages flag issues but allow execution to continue
- **Immutable Audit**: Every decision is recorded with full lineage
- **Multi-Tenant Isolation**: Tenant-specific policies and monitoring
- **Real-Time Monitoring**: Continuous observation and alerting

### Stage Flow

1. **Policy Layer**: Organizational policies and compliance checks
2. **Input Layer**: PII detection, prompt injection prevention, content filtering
3. **Instruction Layer**: Prompt validation and constraint enforcement
4. **Execution Layer**: Tool call validation, rate limiting, cost controls
5. **Output Layer**: Response validation, content filtering, citation verification
6. **Monitoring Layer**: Drift detection, performance tracking, anomaly detection

## Policy Layer Guardrails

### Overview
The Policy Layer is the first stage of the guardrails pipeline, implementing organizational policies, compliance requirements, and access controls before any AI processing begins.

### Components

#### 1. Open Policy Agent (OPA) Integration
- **Purpose**: Centralized policy engine for complex business rules
- **Implementation**: `app.guardrails.opa.check_opa_policy()`
- **Policies**:
  - Tenant-specific usage policies
  - Industry compliance rules (GDPR, HIPAA, SOX)
  - Content restrictions by organization type
  - Geographic data residency requirements

#### 2. Access Control & Authorization
- **Role-Based Access Control (RBAC)**:
  - Founder: Full access to all agents and features
  - Team Member: Limited access based on role
  - Viewer: Read-only access to results
- **Feature Gating**:
  - Premium features based on subscription tier
  - Beta feature access controls
  - Agent-specific permissions

#### 3. Compliance Frameworks
- **GDPR Compliance**:
  - Data processing lawfulness checks
  - Consent verification for EU users
  - Right to erasure enforcement
- **Industry Standards**:
  - SOC 2 Type II controls
  - ISO 27001 alignment
  - NIST Cybersecurity Framework

#### 4. Business Rules Engine
- **Usage Limits**:
  - Monthly API call quotas
  - Concurrent execution limits
  - Resource consumption caps
- **Content Policies**:
  - Prohibited use cases (illegal, harmful content)
  - Industry-specific restrictions
  - Brand safety guidelines

### Configuration
```yaml
policy_layer:
  opa_enabled: true
  opa_endpoint: "http://opa-service:8181"
  compliance_frameworks:
    - gdpr
    - sox
    - hipaa
  default_policies:
    max_monthly_calls: 10000
    max_concurrent_runs: 5
    prohibited_industries:
      - gambling
      - adult_content
```

### Failure Modes
- **Block**: Security violations, compliance breaches
- **Flag**: Policy warnings, usage approaching limits
- **Audit**: All policy decisions logged immutably

## Input Layer Guardrails

### Overview
The Input Layer is the second stage, focusing on sanitizing and validating all incoming data before it reaches the AI models. This layer prevents data leaks, prompt injection attacks, and ensures content safety.

### Components

#### 1. PII Detection & Redaction
- **Microsoft Presidio Integration**:
  - Real-time PII detection for 50+ entity types
  - Configurable redaction strategies (mask, encrypt, remove)
  - Custom entity recognition for business-specific data
- **Supported PII Types**:
  - Personal identifiers (SSN, passport, driver's license)
  - Financial data (credit cards, bank accounts, crypto wallets)
  - Health information (medical record numbers, prescriptions)
  - Contact information (emails, phones, addresses)

#### 2. Prompt Injection Prevention
- **Detection Methods**:
  - Pattern-based detection for known injection techniques
  - ML-based classification for novel attacks
  - Semantic analysis for context manipulation
- **Attack Vectors Covered**:
  - Direct instruction injection
  - Context window poisoning
  - Role confusion attacks
  - System prompt extraction attempts

#### 3. Content Filtering & Toxicity Detection
- **Llama Guard Integration**:
  - Real-time content safety classification
  - Multi-language toxicity detection
  - Contextual harm assessment
- **Content Categories**:
  - Hate speech and discrimination
  - Violence and self-harm
  - Sexual content (age-inappropriate)
  - Illegal activities and fraud

#### 4. Input Validation & Sanitization
- **Schema Validation**:
  - JSON schema enforcement
  - Data type validation
  - Required field verification
- **Size & Rate Limits**:
  - Maximum input length (configurable per tenant)
  - Request rate limiting per user/organization
  - Concurrent request throttling

### Configuration
```yaml
input_layer:
  pii_detection:
    enabled: true
    service: "presidio"
    redaction_strategy: "mask"
    confidence_threshold: 0.8
  
  prompt_injection:
    enabled: true
    detection_methods:
      - pattern_based
      - ml_classifier
      - semantic_analysis
    block_threshold: 0.7
  
  content_filtering:
    enabled: true
    service: "llama_guard"
    categories:
      - hate_speech
      - violence
      - sexual_content
      - illegal_activities
    
  validation:
    max_input_length: 50000
    rate_limit_per_minute: 100
    max_concurrent_requests: 10
```

### Failure Modes
- **Block**: High-confidence PII, prompt injection, toxic content
- **Sanitize**: Low-confidence PII redaction, content warnings
- **Flag**: Suspicious patterns, rate limit approaches

## Instruction Layer Guardrails

### Overview
The Instruction Layer validates and constrains the prompts and instructions sent to AI models, ensuring they align with intended use cases and don't violate system boundaries.

### Components

#### 1. Prompt Template Validation
- **Template Integrity**:
  - Verification against registered prompt templates
  - Variable substitution validation
  - Template version consistency checks
- **Prompt Registry Integration**:
  - Centralized prompt management (AF-048)
  - Version control and rollback capabilities
  - A/B testing support for prompt variations

#### 2. Instruction Constraint Enforcement
- **System Boundary Protection**:
  - Prevention of system prompt modification attempts
  - Role boundary enforcement (user vs system vs assistant)
  - Context window manipulation detection
- **Task Scope Validation**:
  - Verification that instructions match agent capabilities
  - Prevention of out-of-scope task requests
  - Cross-agent instruction isolation

#### 3. Prompt Quality Assessment
- **Clarity & Specificity Metrics**:
  - Instruction ambiguity detection
  - Missing context identification
  - Overly broad request flagging
- **Optimization Suggestions**:
  - Prompt improvement recommendations
  - Best practice compliance checking
  - Performance optimization hints

#### 4. Context Management
- **Context Window Optimization**:
  - Token count validation and optimization
  - Context relevance scoring
  - Automatic context pruning when needed
- **Memory & State Validation**:
  - Session state consistency checks
  - Memory injection prevention
  - Cross-session contamination detection

### Configuration
```yaml
instruction_layer:
  template_validation:
    enabled: true
    strict_mode: true
    allow_custom_templates: false
    
  constraint_enforcement:
    system_boundary_protection: true
    task_scope_validation: true
    role_boundary_enforcement: true
    
  quality_assessment:
    enabled: true
    min_clarity_score: 0.7
    max_ambiguity_threshold: 0.3
    
  context_management:
    max_context_tokens: 32000
    auto_pruning: true
    relevance_threshold: 0.6
```

### Failure Modes
- **Block**: System boundary violations, malformed templates
- **Optimize**: Context window overflow, unclear instructions
- **Flag**: Quality issues, scope mismatches

## Execution Layer Guardrails

### Overview
The Execution Layer monitors and controls tool calls and external API interactions during agent execution, ensuring security, cost control, and proper authorization for all external operations.

### Components

#### 1. Tool Call Validation
- **Schema Enforcement**:
  - JSON schema validation for all tool arguments
  - Required parameter verification
  - Data type and format validation
- **Tool Registry Integration** (AF-047):
  - Centralized tool registration and management
  - Version control for tool definitions
  - Capability-based tool access control

#### 2. Authorization & Access Control
- **Tool-Level Permissions**:
  - Role-based tool access (founder, team member, viewer)
  - Tenant-specific tool allowlists/blocklists
  - API key and credential management
- **Scope Validation**:
  - Verification of tool call scope against user permissions
  - Cross-tenant isolation enforcement
  - Resource boundary protection

#### 3. Rate Limiting & Cost Control
- **API Rate Limiting**:
  - Per-tool rate limits (calls per minute/hour/day)
  - Tenant-level aggregate limits
  - Burst protection with token bucket algorithm
- **Cost Management**:
  - Real-time cost tracking per tool call
  - Budget enforcement and alerts
  - Cost prediction and optimization

#### 4. Security & Safety Controls
- **Dangerous Operation Prevention**:
  - Blocklist for high-risk operations
  - Confirmation requirements for destructive actions
  - Sandbox execution for untrusted tools
- **Data Exfiltration Prevention**:
  - Output size limits per tool call
  - Sensitive data detection in tool responses
  - Cross-service data flow monitoring

### Tool Categories & Controls

#### Research Tools
- **Tavily, SerpAPI, Crunchbase, G2**:
  - Rate limits: 100 calls/hour per tenant
  - Cost cap: $50/month per tenant
  - No special restrictions

#### Engineering Tools
- **GitHub, Stripe, AWS APIs**:
  - Elevated permissions required
  - Audit logging for all operations
  - Confirmation gates for write operations

#### Marketing Tools
- **X, LinkedIn, Resend, ProductHunt**:
  - Content approval workflows
  - Brand safety validation
  - Publishing restrictions

### Configuration
```yaml
execution_layer:
  tool_validation:
    enabled: true
    strict_schema_enforcement: true
    allow_unregistered_tools: false
    
  authorization:
    rbac_enabled: true
    tenant_isolation: strict
    credential_rotation_days: 90
    
  rate_limiting:
    default_rate_limit: "100/hour"
    burst_allowance: 10
    cost_cap_monthly: 1000  # USD
    
  security:
    dangerous_operations_blocked: true
    sandbox_untrusted_tools: true
    max_output_size_mb: 10
```

### Failure Modes
- **Block**: Unauthorized tool access, rate limit exceeded, cost cap reached
- **Queue**: Rate limit approaching, retry with backoff
- **Flag**: Unusual usage patterns, cost approaching limits

## Output Layer Guardrails

### Overview
The Output Layer validates and sanitizes AI-generated responses before they reach users, ensuring content quality, safety, accuracy, and compliance with organizational standards.

### Components

#### 1. Content Safety & Toxicity Detection
- **TruLens Integration**:
  - Real-time toxicity scoring for generated content
  - Multi-dimensional safety assessment
  - Context-aware harm detection
- **Content Categories**:
  - Hate speech and discrimination
  - Violence and threats
  - Sexual or inappropriate content
  - Misinformation and conspiracy theories

#### 2. Factual Accuracy & Citation Verification
- **Citation Validation**:
  - Source URL verification and accessibility
  - Citation format consistency checking
  - Cross-reference validation against knowledge base
- **Fact-Checking Integration**:
  - Real-time fact verification against trusted sources
  - Confidence scoring for factual claims
  - Flagging of potentially false information

#### 3. Quality Assessment
- **Response Completeness**:
  - Verification that all user requirements are addressed
  - Identification of incomplete or partial responses
  - Quality scoring based on comprehensiveness
- **Coherence & Relevance**:
  - Logical flow and structure validation
  - Relevance to original query assessment
  - Consistency with conversation context

#### 4. PII & Sensitive Data Detection
- **Output PII Scanning**:
  - Detection of accidentally generated PII
  - Redaction of sensitive information in responses
  - Cross-tenant data leakage prevention
- **Business Sensitive Information**:
  - Detection of proprietary information
  - Trade secret and confidential data protection
  - Competitive intelligence safeguards

#### 5. Brand Safety & Compliance
- **Brand Guidelines Enforcement**:
  - Tone and voice consistency checking
  - Brand value alignment verification
  - Corporate messaging compliance
- **Legal & Regulatory Compliance**:
  - Industry-specific content restrictions
  - Regulatory disclaimer requirements
  - Legal risk assessment and flagging

### Configuration
```yaml
output_layer:
  content_safety:
    enabled: true
    service: "trulens"
    toxicity_threshold: 0.3
    block_on_high_toxicity: false  # fail-open with flags
    
  citation_verification:
    enabled: true
    verify_urls: true
    require_citations: true
    min_citation_quality: 0.7
    
  quality_assessment:
    enabled: true
    min_completeness_score: 0.8
    min_coherence_score: 0.7
    relevance_threshold: 0.8
    
  pii_detection:
    enabled: true
    redaction_strategy: "mask"
    cross_tenant_check: true
    
  brand_safety:
    enabled: true
    brand_guidelines_check: true
    legal_compliance_check: true
```

### Quality Metrics

#### Response Quality Score
- **Completeness**: 0-1 score based on requirement fulfillment
- **Accuracy**: 0-1 score based on fact-checking results
- **Relevance**: 0-1 score based on query alignment
- **Safety**: 0-1 score based on content safety assessment

#### Citation Quality Score
- **Source Credibility**: Authority and trustworthiness of sources
- **Recency**: How current the cited information is
- **Relevance**: How well citations support the claims
- **Accessibility**: Whether sources are publicly accessible

### Failure Modes
- **Flag**: Quality issues, potential inaccuracies, citation problems
- **Sanitize**: PII redaction, content warnings, disclaimer additions
- **Never Block**: Output layer always fails open to maintain user experience

## Monitoring Layer Guardrails

### Overview
The Monitoring Layer provides continuous observation and analysis of AI system behavior, detecting drift, anomalies, and performance issues to ensure long-term system reliability and safety.

### Components

#### 1. Model Drift Detection
- **Evidently AI Integration**:
  - Statistical drift detection for input/output distributions
  - Concept drift monitoring for changing user patterns
  - Performance drift tracking over time
- **Drift Types Monitored**:
  - Data drift: Changes in input data characteristics
  - Prediction drift: Changes in model output patterns
  - Target drift: Changes in ground truth distributions
  - Feature drift: Changes in feature importance

#### 2. Performance Monitoring
- **Response Quality Tracking**:
  - Quality score trends over time
  - User satisfaction metrics
  - Task completion rates
- **System Performance Metrics**:
  - Response latency percentiles
  - Throughput and capacity utilization
  - Error rates and failure patterns

#### 3. Anomaly Detection
- **Behavioral Anomalies**:
  - Unusual usage patterns per tenant
  - Abnormal cost consumption
  - Suspicious tool usage patterns
- **Content Anomalies**:
  - Unexpected output patterns
  - Novel content types or topics
  - Quality degradation signals

#### 4. Continuous Learning & Feedback
- **Feedback Loop Integration**:
  - User feedback collection and analysis
  - Human-in-the-loop correction tracking
  - Model performance improvement signals
- **A/B Testing Support**:
  - Prompt variation performance comparison
  - Model version effectiveness tracking
  - Feature rollout impact assessment

#### 5. Compliance & Audit Monitoring
- **Regulatory Compliance Tracking**:
  - GDPR compliance metrics
  - Data retention policy adherence
  - Right to erasure request handling
- **Security Event Monitoring**:
  - Failed authentication attempts
  - Suspicious access patterns
  - Data exfiltration attempts

### Configuration
```yaml
monitoring_layer:
  drift_detection:
    enabled: true
    service: "evidently"
    check_interval_hours: 24
    drift_threshold: 0.1
    
  performance_monitoring:
    enabled: true
    quality_tracking: true
    latency_monitoring: true
    error_rate_alerts: true
    
  anomaly_detection:
    enabled: true
    behavioral_anomalies: true
    content_anomalies: true
    sensitivity: "medium"
    
  feedback_integration:
    enabled: true
    user_feedback_collection: true
    hitl_tracking: true
    ab_testing_support: true
    
  compliance_monitoring:
    enabled: true
    gdpr_tracking: true
    audit_trail_validation: true
    security_event_monitoring: true
```

### Alerting & Escalation

#### Alert Severity Levels
- **Critical**: System security breaches, compliance violations
- **High**: Significant drift, performance degradation
- **Medium**: Quality issues, unusual patterns
- **Low**: Informational, trend notifications

#### Escalation Procedures
- **Immediate**: Critical security/compliance issues → Security team
- **1 Hour**: High-severity performance issues → Engineering team
- **24 Hours**: Medium-severity quality issues → Product team
- **Weekly**: Low-severity trends → Analytics team

### Metrics & KPIs

#### System Health Metrics
- **Availability**: 99.9% uptime target
- **Latency**: P95 < 2 seconds for standard requests
- **Error Rate**: < 0.1% for all requests
- **Quality Score**: > 0.8 average across all outputs

#### Business Metrics
- **User Satisfaction**: > 4.5/5 average rating
- **Task Completion Rate**: > 95% for standard workflows
- **Cost Efficiency**: Cost per successful completion
- **Compliance Score**: 100% for regulatory requirements

### Failure Modes
- **Alert**: Drift detected, performance degradation, anomalies
- **Escalate**: Critical issues requiring immediate attention
- **Learn**: Continuous improvement based on monitoring insights

## Implementation Status

### Current Implementation (AF-046)
The AutoFounder AI guardrails pipeline has been implemented with MVP fallbacks:

#### ✅ Completed Components
- **Pipeline Framework**: 6-stage pipeline with fail-closed/fail-open logic
- **Audit & Lineage**: Immutable audit logging for all decisions
- **Policy Layer**: OPA integration with basic policy enforcement
- **Tool Registry**: Centralized tool management and validation
- **Base Integration**: Wired into BaseAgent with optional guardrails parameter

#### 🔄 MVP Fallbacks (Phase 2 Upgrades)
- **Input Layer**: Regex-based PII detection → Presidio integration
- **Content Filtering**: Heuristic toxicity detection → Llama Guard
- **Output Validation**: Basic citation check → TruLens integration
- **Monitoring**: Simple metrics → Evidently AI drift detection
- **Audit Storage**: Local logging → S3 Object Lock immutable storage

### Phase 2 Implementation Plan

#### Priority 1: Security Enhancements
1. **Presidio PII Detection**: Replace regex fallbacks with ML-based detection
2. **Llama Guard Integration**: Advanced content safety classification
3. **S3 Object Lock Audit**: Immutable audit trail with 7-year retention

#### Priority 2: Quality & Monitoring
1. **TruLens Integration**: Advanced output quality assessment
2. **Evidently AI**: Comprehensive drift detection and monitoring
3. **Citation Verification**: Real-time source validation

#### Priority 3: Advanced Features
1. **Prompt Registry**: Full integration with AF-048
2. **Model Router**: Integration with AF-049 LiteLLM routing
3. **A/B Testing**: Prompt and model variation testing

## Configuration & Deployment

### Environment Configuration
```yaml
# Production Configuration
guardrails:
  enabled: true
  fail_closed_on_audit_failure: true
  
  policy_layer:
    opa_endpoint: "https://opa.autofounder.ai"
    compliance_frameworks: ["gdpr", "sox", "hipaa"]
    
  input_layer:
    presidio_endpoint: "https://presidio.autofounder.ai"
    llama_guard_endpoint: "https://llama-guard.autofounder.ai"
    
  output_layer:
    trulens_endpoint: "https://trulens.autofounder.ai"
    citation_verification: true
    
  monitoring_layer:
    evidently_endpoint: "https://evidently.autofounder.ai"
    drift_check_interval: "24h"
```

### Deployment Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Guardrails    │
│   Applications  │───▶│   API Gateway   │───▶│   Pipeline      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 ▼                                 │
                       │                    ┌─────────────────┐                           │
                       │                    │   BaseAgent     │                           │
                       │                    │   (with guards) │                           │
                       │                    └─────────────────┘                           │
                       │                                                                  │
    ┌─────────────────┐│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
    │      OPA        ││  │    Presidio     │  │   Llama Guard   │  │    TruLens      │ │
    │   (Policy)      ││  │   (PII Det.)    │  │  (Content Saf.) │  │  (Quality)      │ │
    └─────────────────┘│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
                       │                                                                  │
    ┌─────────────────┐│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
    │   Evidently     ││  │   S3 Object     │  │   Prometheus    │  │   CloudWatch    │ │
    │  (Monitoring)   ││  │   Lock Audit    │  │   (Metrics)     │  │    (Logs)       │ │
    └─────────────────┘│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
                       └──────────────────────────────────────────────────────────────────┘
```

## Compliance & Audit

### Regulatory Compliance

#### GDPR Compliance
- **Data Processing Lawfulness**: All processing validated against legal basis
- **Consent Management**: Explicit consent tracking and withdrawal handling
- **Right to Erasure**: Automated data deletion across all systems
- **Data Portability**: Export capabilities for user data
- **Privacy by Design**: Default privacy-preserving configurations

#### SOC 2 Type II Controls
- **Security**: Access controls, encryption, vulnerability management
- **Availability**: Uptime monitoring, disaster recovery, incident response
- **Processing Integrity**: Data validation, error handling, quality controls
- **Confidentiality**: Data classification, access restrictions, secure transmission
- **Privacy**: Privacy notice, consent management, data retention

### Audit Trail Requirements

#### Immutable Audit Log
- **What**: Every guardrail decision and outcome
- **When**: Timestamp with nanosecond precision
- **Who**: User, tenant, and agent identification
- **Where**: Geographic location and system component
- **Why**: Policy rule or algorithm that triggered the decision
- **How**: Confidence scores and evidence used

#### Retention & Access
- **Retention Period**: 7 years minimum for compliance
- **Storage**: S3 Object Lock with immutable configuration
- **Access Control**: Role-based access with audit trail
- **Export**: Compliance reporting and legal discovery support

### Incident Response

#### Security Incident Procedures
1. **Detection**: Automated monitoring and alerting
2. **Assessment**: Severity classification and impact analysis
3. **Containment**: Immediate threat mitigation
4. **Investigation**: Root cause analysis and evidence collection
5. **Recovery**: System restoration and validation
6. **Lessons Learned**: Process improvement and prevention

#### Compliance Violation Response
1. **Immediate Notification**: Regulatory authorities within 72 hours
2. **User Notification**: Affected users within required timeframes
3. **Remediation**: Corrective actions and system improvements
4. **Documentation**: Comprehensive incident documentation
5. **Follow-up**: Ongoing monitoring and validation

---

## Conclusion

The AutoFounder AI Comprehensive Guardrails Specification defines a robust, multi-layered security and quality assurance system that ensures safe, compliant, and high-quality AI operations across all aspects of the platform. The 6-layer approach provides defense in depth while maintaining system performance and user experience.

### Key Benefits
- **Security**: Multi-layered protection against threats and attacks
- **Compliance**: Built-in regulatory compliance and audit capabilities
- **Quality**: Continuous monitoring and improvement of AI outputs
- **Scalability**: Tenant-specific policies and monitoring
- **Transparency**: Complete audit trail and explainable decisions

### Next Steps
1. Complete Phase 2 implementation with production-grade services
2. Establish monitoring dashboards and alerting procedures
3. Conduct security and compliance audits
4. Train team on guardrails operation and incident response
5. Continuously improve based on monitoring insights and feedback

This specification serves as the definitive guide for implementing, operating, and maintaining the AutoFounder AI guardrails system to ensure safe, compliant, and high-quality AI operations at scale.
