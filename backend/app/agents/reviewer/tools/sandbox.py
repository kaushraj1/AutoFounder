"""Ephemeral Docker sandbox manager (plan §3.4 nodes 2 & 12, decision D7).

MVP scope: validates the repo's ``Dockerfile`` builds (a failed build is FATAL per
the fallback matrix) and provides ``exec_in`` for running gate tools. When a
container is started, ``exec_in`` runs ``docker exec``; otherwise it falls back to
host-side execution in ``workdir``. Firecracker/gVisor isolation is Phase-2
hardening — Docker-in-Docker on Fargate is itself a separate infra task.

Everything routes through ``_subprocess.run_command`` so tests can mock one seam.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from app.agents.reviewer.schema import SANDBOX_HARD_KILL_SECONDS
from app.agents.reviewer.tools._subprocess import (
    CommandResult,
    binary_available,
    run_command,
)

logger = logging.getLogger("app.agents.reviewer.tools.sandbox")

_BUILD_TIMEOUT = 300.0


class SandboxError(Exception):
    """Sandbox build/spin-up failure (FATAL for the run → escalate)."""


@dataclass(slots=True)
class Sandbox:
    """Handle to an ephemeral execution environment.

    Reconstructable from primitive ``ReviewerState`` fields so it never has to
    live inside the (serialized) graph checkpoint.
    """

    workdir: str
    container_id: str | None = None
    image_tag: str | None = None
    spinup_seconds: float = 0.0


async def spin_up(workdir: str, *, run_id: str, cycle: int = 0) -> Sandbox:
    """Prepare an isolated environment for the repo at ``workdir``.

    If Docker is available and a Dockerfile exists, build the image (FATAL on
    failure). Returns a ``Sandbox`` describing how subsequent ``exec_in`` calls
    should run. Never blocks on Docker when the daemon is absent.
    """
    start = time.perf_counter()
    image_tag: str | None = None

    if binary_available("docker"):
        dockerfile = Path(workdir) / "Dockerfile"
        if dockerfile.exists():
            image_tag = f"reviewer-{run_id}-{cycle}".lower()
            build = await run_command(
                ["docker", "build", "-t", image_tag, "."],
                cwd=workdir,
                timeout=_BUILD_TIMEOUT,
            )
            if not build.ok:
                raise SandboxError(
                    f"Docker build failed (rc={build.returncode}): {build.stderr[:500]}"
                )
            logger.info("Sandbox image built: %s", image_tag)
    else:
        logger.warning(
            "Docker not available — running gates host-side in %s (Phase-2 hardening pending)",
            workdir,
        )

    spinup_seconds = time.perf_counter() - start
    if spinup_seconds > SANDBOX_HARD_KILL_SECONDS:
        logger.warning("Sandbox spin-up %.1fs exceeded hard limit", spinup_seconds)

    return Sandbox(
        workdir=workdir,
        container_id=None,
        image_tag=image_tag,
        spinup_seconds=spinup_seconds,
    )


async def exec_in(sandbox: Sandbox, args: list[str], *, timeout: float = 120.0) -> CommandResult:
    """Run a command inside the sandbox (container if present, else host workdir)."""
    if sandbox.container_id:
        return await run_command(["docker", "exec", sandbox.container_id, *args], timeout=timeout)
    return await run_command(args, cwd=sandbox.workdir, timeout=timeout)


async def teardown(sandbox: Sandbox) -> None:
    """Best-effort cleanup of the container + built image (never raises)."""
    if not (sandbox.container_id or sandbox.image_tag):
        return
    if not binary_available("docker"):
        return
    try:
        if sandbox.container_id:
            await run_command(["docker", "rm", "-f", sandbox.container_id], timeout=30.0)
        if sandbox.image_tag:
            await run_command(["docker", "rmi", "-f", sandbox.image_tag], timeout=30.0)
    except Exception as exc:  # noqa: BLE001 - teardown must never propagate
        logger.warning("Sandbox teardown error (ignored): %s", exc)
