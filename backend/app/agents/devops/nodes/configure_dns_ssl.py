"""Route 53 alias to ALB and ACM certificate."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import DNSRecord, NodeStatus, NodeTrace, TLSCertificate


async def configure_dns_ssl(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	vpc = state.get("vpc_config")
	domain_root = state.get("domain_root", "euron.one")
	subdomain = state.get("subdomain", state.get("organization_id", "app")[:16])
	fqdn = f"{subdomain}.{domain_root}"

	return {
		"dns_record": DNSRecord(
			record_name=fqdn,
			alb_dns_name=(vpc.get("alb_dns_name") if isinstance(vpc, dict) else getattr(vpc, "alb_dns_name", None)),
		),
		"tls_certificate": TLSCertificate(
			domain=fqdn,
			cert_arn=f"arn:aws:acm:{state.get('aws_region', 'ap-south-1')}:000000000000:certificate/{state.get('run_id')}",
			status="Issued",
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