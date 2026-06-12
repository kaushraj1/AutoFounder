"""Strip credentials from URLs before they cross a trust boundary.

A Coder/Orchestrator handoff could carry an authenticated clone URL
(``https://x-access-token:<TOKEN>@github.com/org/repo``). Redact the userinfo
before the URL reaches logs, Slack, the LLM prompt, or the persisted report.
"""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def redact_url(url: str) -> str:
    """Return ``url`` with any ``user:password@`` / ``token@`` userinfo removed.

    Non-URL strings (and ssh-style ``git@host:path``) are returned unchanged —
    only a scheme-qualified netloc's credentials are stripped.
    """
    if not url or "@" not in url:
        return url
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    if not parts.netloc or "@" not in parts.netloc:
        return url
    host = parts.netloc.rsplit("@", 1)[1]
    return urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))
