"""Pydantic schemas for AF-041 Coder Agent (Pillar 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.architect.schema import ArchitectOutput


class GeneratedFile(BaseModel):
    path: str  # e.g. "backend/app/main.py"
    content: str  # raw file content
    language: str  # "python" | "typescript" | "yaml" | "sql" | "dockerfile"


class CoderInput(BaseModel):
    run_id: str
    organization_id: str
    architect_output: ArchitectOutput


class CoderOutput(BaseModel):
    run_id: str
    organization_id: str
    generated_files: list[GeneratedFile]
    backend_files: list[GeneratedFile]  # FastAPI files
    frontend_files: list[GeneratedFile]  # Next.js files
    config_files: list[GeneratedFile]  # Dockerfile, docker-compose, CI, README
    test_files: list[GeneratedFile]  # pytest + jest tests
    total_files: int
    total_lines: int
    total_llm_tokens_used: int
    confidence: str = "high"  # high | medium | low
    warnings: list[str] = Field(default_factory=list)


__all__ = [
    "GeneratedFile",
    "CoderInput",
    "CoderOutput",
    # re-exported for consumers
    "ArchitectOutput",
]
