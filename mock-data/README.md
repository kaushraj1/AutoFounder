# Agent Mock Data

Realistic fixture outputs for the seven pillar agents, using a single coherent scenario: **PawTrail** — subscription dog-walking in Bangalore.

## Pipeline run IDs

| Agent | Run / cycle ID | Folder |
|-------|----------------|--------|
| Strategist | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` | `strategist/` |
| Architect | same parent run | `architect/` |
| Coder | same parent run | `coder/` |
| Reviewer | `b2c3d4e5-f6a7-8901-bcde-f12345678901` | `reviewer/` |
| DevOps | `c3d4e5f6-a7b8-9012-cdef-123456789012` | `devops/` |
| Marketing | `d4e5f6a7-b8c9-0123-defa-234567890123` | `marketing/` |
| LLMOps | `e5f6a7b8-c9d0-1234-efab-345678901234` (weekly cycle) | `llmops/` |

## Files per agent

Each folder contains:

- `output.json` — mock agent output for frontend / API fixtures
- `schema.json` — JSON Schema Draft 2020-12 for validation

## Backend alignment

| Agent | Backend reference |
|-------|-------------------|
| Strategist | `backend/app/agents/strategy/schema.py` |
| Architect | `.claude/developer-plans/03-*-pillar-2-architect-plan.md` |
| Coder | `.claude/developer-plans/04-*-pillar-3-coder-plan.md` |
| Reviewer | `backend/app/agents/reviewer/schema.py` → `ReviewerOutput` |
| DevOps | `backend/app/agents/devops/schema.py` → `DevOpsState` (flat summary in mock) |
| Marketing | `.claude/developer-plans/07-*-pillar-6-marketing-plan.md` → `MarketerOutput` |
| LLMOps | `.claude/developer-plans/08-*-pillar-7-llmops-plan.md` → `LLMOpsOutput` |

## Usage (frontend)

```ts
import strategistOutput from "@/../../mock-data/strategist/output.json";
import strategistSchema from "@/../../mock-data/strategist/schema.json";
```

Or serve via Next.js API route / MSW handlers keyed by `run_id`.
