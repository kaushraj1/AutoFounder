from pathlib import Path

from app.agents.base import PromptRegistryProtocol


class JinjaPromptRegistry(PromptRegistryProtocol):
    """Local prompt registry loading Jinja2 templates from the filesystem."""

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            # Resolved relative to: backend/app/agents/_providers/ -> backend/app/agents/
            base_dir = Path(__file__).parent.parent
        self.base_dir = base_dir

    def get(self, key: str, version: str | None = None) -> str:
        """Read and return the template content from file."""
        parts = key.split("/")
        if len(parts) != 2:
            raise KeyError(f"Invalid prompt key format '{key}'. Expected 'pillar/template_name'")
        pillar, template_name = parts

        # Build path to .j2 file
        prompt_path = self.base_dir / pillar / "prompts" / f"{template_name}.j2"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found at: {prompt_path}")

        return prompt_path.read_text(encoding="utf-8")
