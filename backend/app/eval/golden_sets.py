"""AF-050: Pre-defined golden evaluation cases per agent.

Each list contains raw dicts compatible with ``EvalCase(**case)`` from
``app.eval.harness``. Cases are intentionally minimal so they run fast in CI —
the rubric text instructs the LLM judge on what to look for.

To run these cases::

    from app.eval.harness import EvalHarness, EvalCase
    from app.eval.golden_sets import STRATEGY_GOLDEN_CASES

    cases = [EvalCase(**c) for c in STRATEGY_GOLDEN_CASES]
    report = await EvalHarness(llm_router=router).evaluate("strategy", cases)
"""

from __future__ import annotations

STRATEGY_GOLDEN_CASES: list[dict] = [
    {
        "case_id": "strategy-001",
        "agent_id": "strategy",
        "input": {"idea_raw": "A SaaS tool for managing API documentation"},
        "expected_output": {
            "has_lean_canvas": True,
            "has_personas": True,
            "viability_score_range": [30, 90],
        },
        "rubric": (
            "The strategy output must include a lean canvas with all 9 sections "
            "(problem, solution, unique value proposition, unfair advantage, "
            "customer segments, key metrics, channels, cost structure, revenue streams), "
            "at least 2 buyer personas with name, role, pain points, and goals, "
            "and a viability score between 0–100."
        ),
    },
    {
        "case_id": "strategy-002",
        "agent_id": "strategy",
        "input": {"idea_raw": "An AI fitness coaching mobile app for busy professionals"},
        "expected_output": {
            "has_lean_canvas": True,
            "has_personas": True,
            "viability_score_range": [40, 95],
            "domain": "health_fitness",
        },
        "rubric": (
            "The strategy output should identify the health/fitness domain, include a "
            "lean canvas, at least one persona representing a busy professional, "
            "and a viability score that reflects the competitive but viable nature "
            "of the consumer health tech market."
        ),
    },
]

ARCHITECT_GOLDEN_CASES: list[dict] = [
    {
        "case_id": "architect-001",
        "agent_id": "architect",
        "input": {
            "idea_normalised": "SaaS tool for managing API documentation",
            "viability_band": "viable",
            "prd_preview": "A web platform that lets teams write, version, and publish API docs.",
        },
        "expected_output": {
            "has_erd": True,
            "has_openapi": True,
            "has_stack": True,
            "stack_keys": ["frontend", "backend", "database"],
            "has_requirements": True,
        },
        "rubric": (
            "The architect output must include a valid Mermaid erDiagram with at least "
            "2 entities and required columns (id, created_at, updated_at), a non-empty "
            "OpenAPI 3.x spec with at least one path, a tech stack with frontend, backend, "
            "and database keys, and at least 3 functional requirements."
        ),
    },
    {
        "case_id": "architect-002",
        "agent_id": "architect",
        "input": {
            "idea_normalised": "AI fitness coaching mobile app",
            "viability_band": "viable",
            "prd_preview": "A mobile app powered by AI to create personalised workout plans.",
        },
        "expected_output": {
            "has_erd": True,
            "has_openapi": True,
            "has_stack": True,
            "has_auth_strategy": True,
        },
        "rubric": (
            "The architect output must include an ERD with a User entity, an OpenAPI spec "
            "covering at least a /workouts endpoint, a stack identifying a mobile-capable "
            "frontend (React Native or Flutter), and an auth strategy section."
        ),
    },
]

CODER_GOLDEN_CASES: list[dict] = [
    {
        "case_id": "coder-001",
        "agent_id": "coder",
        "input": {
            "feature": "User registration endpoint",
            "stack": {"backend": "FastAPI", "database": "PostgreSQL"},
            "requirements": [
                "POST /auth/register accepts email + password",
                "Hash password with bcrypt",
            ],
        },
        "expected_output": {
            "has_code": True,
            "language": "python",
            "has_tests": True,
            "passes_lint": True,
        },
        "rubric": (
            "The coder output must include valid Python code implementing a FastAPI "
            "POST /auth/register endpoint that hashes passwords with bcrypt, "
            "a matching pytest test file, and code that would pass ruff linting "
            "(no unused imports, proper type hints)."
        ),
    },
]
