"""Jinja2 prompt loader for the Marketing Agent (AF-044).

Loads templates from the local prompts/ directory.
When Purnima's Prompt Registry (AF-048) is live, swap this out
by changing `render()` to call the registry instead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_PROMPTS_DIR = Path(__file__).parent / "prompts"

_env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    undefined=StrictUndefined,
    autoescape=False,
)


def render(template_name: str, **variables: Any) -> str:
    """Render a Jinja2 prompt template with the given variables.

    Args:
        template_name: filename without extension, e.g. "analyse_brand"
        **variables: template context variables

    Returns:
        Rendered prompt string ready to send to the LLM.

    Raises:
        jinja2.UndefinedError: if a required variable is missing.
        jinja2.TemplateNotFound: if the template file does not exist.
    """
    template = _env.get_template(f"{template_name}.j2")
    return template.render(**variables)
