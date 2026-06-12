"""DevOpsState and sub-models. Ported from devops-agent.md sec.2."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

# Enums --------------------------------------------------------------------

class NodeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


class DeployStrategy(StrEnum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"


class TerraformAction(StrEnum):
    PLAN = "plan"
    APPLY = "apply"
    DESTROY = "destroy"


class InfraStatus(StrEnum):
    NOT_STARTED = "not_started"
    PROVISIONING = "provisioning"
    READY = "ready"
    FAILED = "failed"


class DeployStatus(StrEnum):
    NOT_STARTED = "not_started"
    SYNCING = "syncing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


# Input from Coder Agent ---------------------------------------------------

class ServiceManifest(BaseModel):
    name: str
    image_uri: str
    port: int
    replicas_baseline: int = 2
    health_check_path: str = "/health"
    env_secret_refs: list[str] = Field(default_factory=list)
    resource_requests: dict[str, str] = Field(
        default_factory=lambda: {"cpu": "250m", "memory": "512Mi"}
    )
    resource_limits: dict[str, str] = Field(
        default_factory=lambda: {"cpu": "1000m", "memory": "2Gi"}
    )


# Networking ---------------------------------------------------------------

class VPCConfig(BaseModel):
    vpc_id: str | None = None
    cidr_block: str = "10.0.0.0/16"
    public_subnet_ids: list[str] = Field(default_factory=list)
    private_subnet_ids: list[str] = Field(default_factory=list)
    availability_zones: list[str] = Field(default_factory=lambda: ["ap-south-1a", "ap-south-1b"])
    nat_gateway_id: str | None = None
    internet_gateway_id: str | None = None
    # Role -> SG ID. Roles: 'alb', 'ecs_tasks', 'redis', 'rds'.
    security_group_ids: dict[str, str] = Field(default_factory=dict)
    alb_arn: str | None = None
    alb_dns_name: str | None = None


# Compute (ECS Fargate) ----------------------------------------------------

class ECSService(BaseModel):
    service_name: str
    task_def_arn: str | None = None
    desired_count: int = 2
    cpu: int = 512
    memory_mb: int = 1024
    container_port: int
    target_group_arn: str | None = None
    health_check_path: str = "/health"
    status: InfraStatus = InfraStatus.NOT_STARTED


class ECSCluster(BaseModel):
    cluster_name: str | None = None
    cluster_arn: str | None = None
    region: str = "ap-south-1"
    capacity_providers: list[str] = Field(default_factory=lambda: ["FARGATE", "FARGATE_SPOT"])
    services: list[ECSService] = Field(default_factory=list)
    status: InfraStatus = InfraStatus.NOT_STARTED


# Data layer ---------------------------------------------------------------

class RDSInstance(BaseModel):
    # Supabase is reserved for the AutoFounder control-plane; tenant MVPs use RDS.
    kind: Literal["rds"] = "rds"
    db_instance_identifier: str | None = None
    engine: str = "postgres"
    engine_version: str = "16.3"
    instance_class: str = "db.t4g.micro"
    allocated_storage_gb: int = 20
    storage_type: str = "gp3"
    storage_encrypted: bool = True
    multi_az: bool = False
    publicly_accessible: bool = False
    db_subnet_group_name: str | None = None
    vpc_security_group_id: str | None = None
    endpoint: str | None = None
    port: int = 5432
    db_name: str = "app"
    master_username: str = "app_admin"
    credentials_secret_name: str | None = None
    credentials_secret_arn: str | None = None
    backup_retention_days: int = 7
    deletion_protection: bool = False
    status: InfraStatus = InfraStatus.NOT_STARTED


class ElastiCacheCluster(BaseModel):
    cluster_id: str | None = None
    engine: str = "redis"
    engine_version: str = "7.1"
    node_type: str = "cache.t3.micro"
    num_cache_nodes: int = 1
    endpoint: str | None = None
    port: int = 6379
    status: InfraStatus = InfraStatus.NOT_STARTED


class S3Bucket(BaseModel):
    bucket_name: str | None = None
    region: str = "ap-south-1"
    versioning_enabled: bool = True
    encryption: str = "AES256"
    public_access_blocked: bool = True


# Secrets ------------------------------------------------------------------

class SecretRef(BaseModel):
    secret_name: str
    secret_arn: str | None = None
    keys: list[str] = Field(default_factory=list)


# ECS task defs / CodeDeploy ----------------------------------------------

class ECSTaskDef(BaseModel):
    service_name: str
    family: str
    task_def_json: str
    container_image: str
    log_group: str
    execution_role_arn: str | None = None
    task_role_arn: str | None = None


class CodeDeployApp(BaseModel):
    app_name: str
    deployment_group: str
    appspec_yaml: str
    deployment_config: str = "CodeDeployDefault.ECSAllAtOnce"
    compute_platform: str = "ECS"
    health_status: str | None = None


# DNS / TLS ----------------------------------------------------------------

class DNSRecord(BaseModel):
    hosted_zone_id: str | None = None
    record_name: str
    record_type: str = "A"
    alb_dns_name: str | None = None
    ttl: int = 300


class TLSCertificate(BaseModel):
    domain: str
    cert_arn: str | None = None
    issuer: str = "letsencrypt-prod"
    status: str | None = None


# Monitoring ---------------------------------------------------------------

class CloudWatchAlarm(BaseModel):
    alarm_name: str
    metric_name: str
    namespace: str
    threshold: float
    comparison: str
    evaluation_periods: int = 2
    period_seconds: int = 60
    sns_topic_arn: str | None = None


class MonitoringConfig(BaseModel):
    cloudwatch_alarms: list[CloudWatchAlarm] = Field(default_factory=list)
    prometheus_scrape_configs: list[str] = Field(default_factory=list)
    grafana_dashboard_url: str | None = None
    log_group_name: str | None = None
    log_retention_days: int = 90


# CI/CD --------------------------------------------------------------------

class CICDConfig(BaseModel):
    workflow_file_path: str
    workflow_yaml: str
    codedeploy_app_name: str | None = None
    ecr_registry: str | None = None


# Smoke test ---------------------------------------------------------------

class SmokeTestResult(BaseModel):
    endpoint: str
    status_code: int
    latency_ms: float
    passed: bool
    error: str | None = None


# Execution metadata -------------------------------------------------------

class NodeTrace(BaseModel):
    node: str
    status: NodeStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    retry_count: int = 0
    terraform_output: str | None = None


class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_seconds: list[int] = Field(default_factory=lambda: [10, 30, 60])


# Root state ---------------------------------------------------------------

class DevOpsState(BaseModel):
    """LangGraph state threaded through every node in the DevOps subgraph."""

    # extra='ignore' lets the CoderOutput dummy carry extra fields without failing.
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    # Identity
    run_id: UUID = Field(default_factory=uuid4)
    parent_run_id: UUID = Field(..., description="Coder Agent run_id")
    grandparent_run_id: UUID = Field(..., description="Architect Agent run_id")
    organization_id: str = Field(..., description="Validated from JWT claims")

    # Input from Coder
    idea_normalised: str
    domain: str
    repo_url: str
    services: list[ServiceManifest] = Field(default_factory=list)
    overall_pattern: str = "modular_monolith"
    aws_region: str = "ap-south-1"
    deploy_strategy: DeployStrategy = DeployStrategy.ROLLING
    estimated_monthly_cost_usd: float = 0.0

    # HITL spend gate
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approval_comment: str | None = None
    approval_timeout_at: datetime | None = None

    # Forward-compat discriminator for a future stack-agnostic dispatcher.
    compute_target: str = "ecs_fargate"

    # Infrastructure outputs
    vpc_config: VPCConfig | None = None
    ecs_cluster: ECSCluster | None = None
    rds_instance: RDSInstance | None = None
    elasticache_cluster: ElastiCacheCluster | None = None
    s3_bucket: S3Bucket | None = None
    secrets: list[SecretRef] = Field(default_factory=list)

    # Deployment artefacts
    task_defs: list[ECSTaskDef] = Field(default_factory=list)
    codedeploy_app: CodeDeployApp | None = None
    deploy_status: DeployStatus = DeployStatus.NOT_STARTED

    # Post-deploy
    dns_record: DNSRecord | None = None
    tls_certificate: TLSCertificate | None = None
    live_url: str | None = None
    monitoring_config: MonitoringConfig | None = None
    cicd_config: CICDConfig | None = None

    # Smoke
    smoke_test_results: list[SmokeTestResult] = Field(default_factory=list)
    smoke_tests_passed: bool = False

    # Final output
    deploy_report_markdown: str | None = None

    # Terraform
    terraform_plan_output: str | None = None
    terraform_state_s3_key: str | None = None

    # Execution metadata
    node_traces: list[NodeTrace] = Field(default_factory=list)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    total_llm_tokens_used: int = 0
    total_tool_calls: int = 0
    error_count: int = 0

    # LangGraph message channel (Annotated[..., add_messages] reattached in graph.py
    # once langgraph is on the path).
    messages: list[Any] = Field(default_factory=list)

    # Terminal flags
    is_complete: bool = False
    fatal_error: str | None = None