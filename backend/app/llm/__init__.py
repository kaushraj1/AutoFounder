"""AF-049: LLM routing package.

Exports the task-class based LLMRouter and the TASK_CLASS_MODEL_MAP.
"""

from app.llm.router import LLMRouter, TASK_CLASS_MODEL_MAP

__all__ = ["LLMRouter", "TASK_CLASS_MODEL_MAP"]
