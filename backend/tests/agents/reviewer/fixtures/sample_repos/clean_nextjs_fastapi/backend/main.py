"""Clean sample FastAPI backend (no seeded defects)."""


def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def healthy() -> dict[str, str]:
    return {"status": "ok"}
