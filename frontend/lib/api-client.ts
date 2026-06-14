/**
 * Typed API client for the AutoFounder AI backend.
 * Matches the REST contract defined in backend/app/api/v1/.
 */

import type {
  GateDecision,
  GateRead,
  IdeaCreate,
  PaginatedResponseEnvelope,
  ResponseEnvelope,
  Run,
} from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}/v1${path}`, {
    headers: {
      'Content-Type': 'application/json',
      // TODO: attach Bearer token from Supabase session in Phase 2
      ...options?.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const message =
      (body as { error?: { message?: string } })?.error?.message ??
      `HTTP ${res.status}`
    throw new Error(message)
  }

  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// Ideas
// ---------------------------------------------------------------------------

/**
 * Submit a startup idea and start a validation run.
 * POST /v1/ideas
 */
export async function createIdea(
  payload: IdeaCreate
): Promise<ResponseEnvelope<Run>> {
  return apiFetch<ResponseEnvelope<Run>>('/ideas', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// ---------------------------------------------------------------------------
// Runs
// ---------------------------------------------------------------------------

/**
 * List all runs for the current org (cursor-paginated).
 * GET /v1/runs
 */
export async function listRuns(
  opts: { limit?: number; cursor?: string; order?: 'asc' | 'desc' } = {}
): Promise<PaginatedResponseEnvelope<Run>> {
  const params = new URLSearchParams()
  if (opts.limit) params.set('limit', String(opts.limit))
  if (opts.cursor) params.set('cursor', opts.cursor)
  if (opts.order) params.set('order', opts.order)
  const qs = params.toString() ? `?${params}` : ''
  return apiFetch<PaginatedResponseEnvelope<Run>>(`/runs${qs}`)
}

/**
 * Get a single run by ID.
 * GET /v1/runs/:id
 */
export async function getRun(runId: string): Promise<ResponseEnvelope<Run>> {
  return apiFetch<ResponseEnvelope<Run>>(`/runs/${runId}`)
}

/**
 * Cancel a run.
 * DELETE /v1/runs/:id
 */
export async function cancelRun(runId: string): Promise<ResponseEnvelope<boolean>> {
  return apiFetch<ResponseEnvelope<boolean>>(`/runs/${runId}`, {
    method: 'DELETE',
  })
}

// ---------------------------------------------------------------------------
// Gates (HITL)
// ---------------------------------------------------------------------------

/**
 * List pending HITL gates for a run.
 * GET /v1/runs/:runId/gates
 */
export async function listGates(
  runId: string
): Promise<ResponseEnvelope<GateRead[]>> {
  return apiFetch<ResponseEnvelope<GateRead[]>>(`/runs/${runId}/gates`)
}

/**
 * Approve or reject a HITL gate.
 * POST /v1/runs/:runId/gates/:gateId
 */
export async function approveGate(
  runId: string,
  gateId: string,
  decision: GateDecision
): Promise<ResponseEnvelope<GateRead>> {
  return apiFetch<ResponseEnvelope<GateRead>>(
    `/runs/${runId}/gates/${gateId}`,
    {
      method: 'POST',
      body: JSON.stringify(decision),
    }
  )
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function getHealth(): Promise<{ status: string; service: string }> {
  return apiFetch<{ status: string; service: string }>('/health')
}
