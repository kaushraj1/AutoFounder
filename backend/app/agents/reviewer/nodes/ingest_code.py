"""Node 1 — ingest_code: clone/locate the repo and detect languages (plan §3.4)."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from app.agents.reviewer.schema import CodeArtifact, ReviewerState
from app.agents.reviewer.tools._subprocess import binary_available, run_command

logger = logging.getLogger("app.agents.reviewer.nodes.ingest_code")

_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
_PY_EXT = {".py"}
_TS_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
_MAX_ARTIFACTS = 100


async def ingest_code(state: ReviewerState, agent: Any) -> dict[str, Any]:
    """Validate inputs, resolve a workdir, and inventory source files.

    FATAL (sets ``fatal_error``) when there is nothing to test — the run cannot
    proceed and the router sends it straight to ``error_handler``.
    """
    if not state.repo_url and not state.local_path:
        return {"fatal_error": "No repo_url or local_path provided — nothing to test"}

    workdir = await _resolve_workdir(state)
    if workdir is None:
        return {
            "fatal_error": (
                f"Could not obtain a working copy of {state.repo_url} "
                "(no local_path and git clone unavailable/failed)"
            )
        }

    artifacts, has_python, has_typescript = _inventory(workdir)
    if not artifacts:
        return {"fatal_error": f"No source files found under {workdir}"}

    logger.info(
        "Ingested %d artifacts from %s (python=%s, typescript=%s)",
        len(artifacts),
        workdir,
        has_python,
        has_typescript,
    )
    return {
        "workdir": workdir,
        "code_artifacts": artifacts,
        "has_python": has_python,
        "has_typescript": has_typescript,
    }


async def _resolve_workdir(state: ReviewerState) -> str | None:
    if state.local_path and Path(state.local_path).is_dir():
        return state.local_path
    if not state.repo_url or not binary_available("git"):
        return None
    # Reject values that git would parse as options (argument-injection guard).
    if state.repo_url.startswith("-"):
        logger.warning("Refusing repo_url that looks like a git option: %s", state.repo_url)
        return None
    target = tempfile.mkdtemp(prefix=f"reviewer-{state.run_id}-")
    args = ["git", "clone", "--depth", "1"]
    if state.branch and not state.branch.startswith("-"):
        args += ["--branch", state.branch]
    # `--` terminates options so a hostile repo_url/target can't be read as a flag.
    args += ["--", state.repo_url, target]
    res = await run_command(args, timeout=120.0)
    if not res.ok:
        logger.warning("git clone failed: %s", res.stderr[:300])
        return None
    return target


def _inventory(workdir: str) -> tuple[list[CodeArtifact], bool, bool]:
    artifacts: list[CodeArtifact] = []
    has_python = False
    has_typescript = False

    for root, dirs, files in os.walk(workdir):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in files:
            ext = Path(name).suffix.lower()
            if name == "package.json":
                has_typescript = True
            language: str | None = None
            if ext in _PY_EXT:
                has_python = True
                language = "python"
            elif ext in _TS_EXT:
                has_typescript = True
                language = "typescript"
            elif name == "Dockerfile":
                language = "dockerfile"
            if language is None:
                continue
            if len(artifacts) < _MAX_ARTIFACTS:
                full = Path(root) / name
                artifacts.append(
                    CodeArtifact(
                        path=os.path.relpath(full, workdir),
                        language=language,
                        lines=_count_lines(full),
                    )
                )
    return artifacts, has_python, has_typescript


def _count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0
