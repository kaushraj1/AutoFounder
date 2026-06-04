# @autofounder-ai/api-client

Typed TypeScript client for the AutoFounder AI backend, consumed by the web and mobile apps.

```ts
import { AutoFounderClient } from "@autofounder-ai/api-client";

const api = new AutoFounderClient(process.env.NEXT_PUBLIC_API_URL!);
const run = await api.submitIdea({ text: "A marketplace for..." });
const status = await api.getRun(run.id);
```

**Phase 1:** hand-written minimal client (health, ideas, runs).
**Phase 2:** auto-generated from the backend OpenAPI spec so types stay in lockstep with the API.
