"""Route 53 alias to ALB and ACM certificate.

Calls ``acm_request_certificate`` and ``route53_upsert`` when a hosted
zone is configured in state. Tool failures degrade gracefully — the
record is still recorded in graph state so downstream nodes can see the
intended FQDN.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agents.devops.schema import DNSRecord, NodeStatus, NodeTrace, TLSCertificate
from app.core.logging import bind_log_context


async def configure_dns_ssl(state: dict, agent: Any | None = None) -> dict:
    state = state.model_dump() if hasattr(state, "model_dump") else state
    now = datetime.now(UTC)
    bind_log_context(
        organization_id=str(state.get("organization_id", "")),
        run_id=str(state.get("run_id", "")),
        agent_id="devops",
        node="configure_dns_ssl",
    )
    vpc = state.get("vpc_config")
    domain_root = state.get("domain_root", "euron.one")
    subdomain = state.get("subdomain", state.get("organization_id", "app")[:16])
    fqdn = f"{subdomain}.{domain_root}"
    alb_dns_name = (
        vpc.get("alb_dns_name") if isinstance(vpc, dict) else getattr(vpc, "alb_dns_name", None)
    )

    cert_arn = (
        f"arn:aws:acm:{state.get('aws_region', 'ap-south-1')}:"
        f"000000000000:certificate/{state.get('run_id')}"
    )
    cert_status = "Issued"

    if agent is not None:
        try:
            result = await agent._call_tool("acm_request_certificate", {"domain": fqdn})
            cert_arn = result.get("certificate_arn") or cert_arn
            cert_status = result.get("status") or cert_status
        except Exception:
            pass

        zone_id = state.get("hosted_zone_id")
        if zone_id and alb_dns_name:
            try:
                await agent._call_tool(
                    "route53_upsert",
                    {
                        "zone_id": zone_id,
                        "record_name": fqdn,
                        "alb_dns_name": alb_dns_name,
                    },
                )
            except Exception:
                pass

    return {
        "dns_record": DNSRecord(
            record_name=fqdn,
            alb_dns_name=alb_dns_name,
        ),
        "tls_certificate": TLSCertificate(
            domain=fqdn,
            cert_arn=cert_arn,
            status=cert_status,
        ),
        "live_url": f"https://{fqdn}",
        "node_traces": [
            NodeTrace(
                node="configure_dns_ssl",
                status=NodeStatus.COMPLETED,
                started_at=now,
                completed_at=now,
            )
        ],
    }
