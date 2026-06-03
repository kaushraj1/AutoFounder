"""Seed script for local development.

Phase 1 has no persisted seed data (the run store is in-memory). This placeholder keeps the
``scripts/`` location stable; Sprint 1 will insert demo organizations and sample runs once the
UDAL-backed persistence lands. Run with: ``uv run python scripts/seed.py``.
"""


def main() -> None:
    print("No seed data in Phase 1 (in-memory run store). Implemented in Sprint 1.")


if __name__ == "__main__":
    main()
