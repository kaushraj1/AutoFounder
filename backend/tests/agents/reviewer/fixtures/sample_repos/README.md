# Reviewer sample repos (fixtures)

Deterministic example repositories for the Reviewer agent (plan §9.3). They are
**not** collected by pytest (no `test_*.py` / `*_test.py` filenames; the package
conftest also sets `collect_ignore_glob`). Integration tests mock the gate tools,
so these are used for ingest/language-detection and the local e2e harness
(`python -m app.agents.reviewer.e2e_test --repo <dir> --mock-llm`).

| Repo | Seeded defects | Expected verdict |
|---|---|---|
| `clean_nextjs_fastapi` | none | approved, 0 cycles |
| `lint_errors` | fixable lint errors | approved, 1 cycle |
| `failing_unit_tests` | logic bugs | approved, ~2 cycles (patch source) |
| `sql_injection` | OWASP A03 (critical, not fixable) | **escalate** (hard block) |
| `low_coverage` | passing tests, low coverage | **escalate** (coverage gate) |
