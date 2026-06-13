"""Shared fakes for DevOps tests.

Exposes a fake LLM router that returns valid JSON / markdown for each of
the four LLM-driven DevOps nodes, so integration tests don't have to
mock four separate completions individually.
"""

from __future__ import annotations

import json
from typing import Any


class FakeDevOpsLLMRouter:
    """Mimics ``LLMRouterProtocol.complete`` for DevOps task classes.

    Inspects the prompt to read the services list and returns a canned
    response for each ``task_class``. Markdown for render_deploy_report,
    JSON for the others.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def complete(self, *, task_class: str, prompt: str, **kw: Any) -> str:
        self.calls.append((task_class, prompt))
        if task_class == "build_task_defs":
            return json.dumps(
                {
                    "task_defs": _task_defs_from_prompt(prompt),
                }
            )
        if task_class == "configure_cicd":
            return json.dumps(
                {
                    "workflow_yaml": (
                        "name: deploy\n"
                        "on:\n  push:\n    branches: [main]\n"
                        "jobs:\n"
                        "  deploy:\n"
                        "    runs-on: ubuntu-latest\n"
                        "    steps:\n"
                        "      - uses: actions/checkout@v4\n"
                        "      - uses: aws-actions/configure-aws-credentials@v4\n"
                        "        with:\n"
                        "          role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}\n"
                        "          aws-region: us-east-1\n"
                    ),
                }
            )
        if task_class == "configure_monitoring":
            return json.dumps(
                {
                    "alarms": [
                        {
                            "name_suffix": "5xx",
                            "metric_name": "HTTPCode_Target_5XX_Count",
                            "namespace": "AWS/ApplicationELB",
                            "threshold": 5.0,
                            "comparison": "GreaterThanThreshold",
                            "evaluation_periods": 2,
                            "period_seconds": 60,
                        },
                        {
                            "name_suffix": "cpu",
                            "metric_name": "CPUUtilization",
                            "namespace": "AWS/ECS",
                            "threshold": 85.0,
                            "comparison": "GreaterThanThreshold",
                            "evaluation_periods": 2,
                            "period_seconds": 60,
                        },
                    ],
                    "log_retention_days": 30,
                }
            )
        if task_class == "render_deploy_report":
            return (
                "## Overview\n\n"
                "Deployment healthy.\n\n"
                "## Services\n\n- api\n\n"
                "## Monitoring\n\n- 5xx\n- cpu\n\n"
                "## CI/CD\n\n.github/workflows/deploy.yml\n\n"
                "## Cost & next steps\n\n- watch 5xx alarm\n"
            )
        raise ValueError(f"FakeDevOpsLLMRouter: unknown task_class {task_class}")


def _task_defs_from_prompt(prompt: str) -> list[dict[str, Any]]:
    """Extract services from the rendered prompt and emit one sizing per service.

    Falls back to a single-entry default if parsing fails.
    """
    try:
        marker = "Services:\n"
        idx = prompt.index(marker) + len(marker)
        tail = prompt[idx:]
        end = tail.index("\n\nReturn ONLY")
        services_json = tail[:end].strip()
        services = json.loads(services_json)
    except (ValueError, json.JSONDecodeError):
        services = [{"name": "default", "port": 8080}]

    out: list[dict[str, Any]] = []
    for s in services:
        out.append(
            {
                "service_name": s["name"],
                "cpu_units": 256,
                "memory_mb": 512,
                "container_port": s["port"],
                "log_retention_days": 30,
            }
        )
    return out
