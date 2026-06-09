"""GitHub integration: post the review comment + apply heal patches (plan §3.4).

- ``post_pr_comment`` posts the consolidated report to the PR (no-op + None when
  ``GITHUB_TOKEN`` is missing — the report is still stored in S3).
- ``apply_patches`` writes the healer's patched files into the workdir (and stages
  them with git when available) so the next sandbox cycle re-tests the fix.
  Real remote commits via the GitHub API are Phase-2; MVP heals the local clone.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.agents.reviewer.tools._subprocess import binary_available, run_command
from app.agents.reviewer.tools.sandbox import Sandbox

logger = logging.getLogger("app.agents.reviewer.tools.github")


def _parse_owner_repo(repo_url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub URL or ``owner/repo`` slug."""
    cleaned = repo_url.strip().removesuffix(".git")
    if "github.com" in cleaned:
        cleaned = cleaned.split("github.com", 1)[1].lstrip(":/")
    parts = [p for p in cleaned.split("/") if p]
    if len(parts) < 2:
        return None
    return parts[-2], parts[-1]


async def post_pr_comment(
    repo_url: str,
    pr_number: int,
    body: str,
    *,
    token: str | None = None,
) -> str | None:
    """Post a PR comment; return its URL, or None if it could not be posted."""
    if not token:
        logger.warning("GITHUB_TOKEN not configured — skipping PR comment")
        return None
    if pr_number <= 0:
        logger.info("No PR number — skipping PR comment")
        return None
    owner_repo = _parse_owner_repo(repo_url)
    if owner_repo is None:
        logger.warning("Could not parse owner/repo from %s — skipping PR comment", repo_url)
        return None
    owner, repo = owner_repo

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"body": body}, headers=headers)
            resp.raise_for_status()
            return resp.json().get("html_url")
    except httpx.HTTPError as exc:
        logger.warning("Failed to post PR comment: %s", exc)
        return None


async def apply_patches(
    sandbox: Sandbox,
    files: dict[str, str],
    *,
    commit_message: str = "fix: reviewer self-heal",
) -> list[str]:
    """Write patched file contents into the workdir; stage with git if available.

    Returns the relative paths actually written. Refuses to escape the workdir.
    """
    workdir = Path(sandbox.workdir).resolve()
    written: list[str] = []
    for rel_path, content in files.items():
        candidate = Path(rel_path)
        if candidate.is_absolute() or candidate.drive:
            logger.warning("Refusing absolute patch path: %s", rel_path)
            continue
        target = (workdir / rel_path).resolve()
        # True path-boundary check (not a string prefix) — blocks ../ and sibling escapes.
        if target != workdir and workdir not in target.parents:
            logger.warning("Refusing to patch outside workdir: %s", rel_path)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel_path)

    if written and binary_available("git") and (workdir / ".git").exists():
        await run_command(["git", "add", *written], cwd=str(workdir), timeout=30.0)
        await run_command(["git", "commit", "-m", commit_message], cwd=str(workdir), timeout=30.0)

    return written
