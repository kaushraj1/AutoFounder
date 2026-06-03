"""Idea intake schema."""

from pydantic import BaseModel, ConfigDict, Field


class IdeaCreate(BaseModel):
    """A founder's raw startup idea submitted to start a validation run."""

    model_config = ConfigDict(strict=True)

    text: str = Field(
        min_length=10,
        max_length=10_000,
        description="The raw startup idea in plain text.",
    )
