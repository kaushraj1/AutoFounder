"""Shared async subprocess runner for the Reviewer's CLI-based tools.

Every scanner / linter / test runner / sandbox call goes through ``run_command``
so timeouts, missing-binary detection, and output capture behave identically.
No third-party dependency — the standard library ``asyncio`` subprocess API is
sufficient and works on every CI host.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass

logger = logging.getLogger("app.agents.reviewer.tools.subprocess")


@dataclass(slots=True)
class CommandResult:
    """Outcome of a subprocess invocation."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def binary_available(binary: str) -> bool:
    """True if ``binary`` is resolvable on PATH (graceful-skip gate)."""
    return shutil.which(binary) is not None


async def run_command(
    args: list[str],
    *,
    cwd: str | None = None,
    timeout: float = 120.0,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run ``args`` and capture stdout/stderr with a hard timeout.

    Never raises on a non-zero exit code (scanners legitimately exit non-zero
    when they find issues) — callers inspect ``returncode``. Raises only if the
    binary cannot be spawned at all.
    """
    # Log only the program + arg count — never the full argv, which may carry a
    # credentialed clone URL or token.
    logger.debug(
        "run_command: %s (%d args, cwd=%s timeout=%.0fs)", args[0], len(args), cwd, timeout
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Binary not found: {args[0]}") from exc

    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        logger.warning("Command timed out after %.0fs: %s", timeout, args[0])
        return CommandResult(returncode=-1, stdout="", stderr="timeout", timed_out=True)

    return CommandResult(
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
    )
