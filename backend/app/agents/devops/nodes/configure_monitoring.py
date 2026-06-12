"""CloudWatch alarms, Prometheus scrape, Grafana."""

from __future__ import annotations

from datetime import UTC, datetime

from app.agents.devops.schema import CloudWatchAlarm, MonitoringConfig, NodeStatus, NodeTrace


async def configure_monitoring(state: dict) -> dict:
	state = state.model_dump() if hasattr(state, "model_dump") else state
	now = datetime.now(UTC)
	org = state.get("organization_id", "tenant")
	run = str(state.get("run_id", "run"))[:8]
	cfg = MonitoringConfig(
		cloudwatch_alarms=[
			CloudWatchAlarm(
				alarm_name=f"{org[:12]}-{run}-5xx",
				metric_name="HTTPCode_Target_5XX_Count",
				namespace="AWS/ApplicationELB",
				threshold=5,
				comparison="GreaterThanThreshold",
			),
			CloudWatchAlarm(
				alarm_name=f"{org[:12]}-{run}-cpu",
				metric_name="CPUUtilization",
				namespace="AWS/ECS",
				threshold=85,
				comparison="GreaterThanThreshold",
			),
		],
		prometheus_scrape_configs=["job_name: ecs-services"],
		grafana_dashboard_url=f"https://grafana.example.com/d/{run}",
		log_group_name=f"/ecs/{org}/{run}",
	)
	return {
		"monitoring_config": cfg,
		"node_traces": [
			NodeTrace(
				node="configure_monitoring",
				status=NodeStatus.COMPLETED,
				started_at=now,
				completed_at=now,
			)
		],
	}