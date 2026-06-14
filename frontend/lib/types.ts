/**
 * TypeScript types matching the AutoFounder AI backend schemas.
 */

export type RunStatus =
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled'

export type RunPillar =
  | 'strategy'
  | 'research'
  | 'product_planner'
  | 'engineering'
  | 'review'
  | 'devops'
  | 'marketing'

export interface Run {
  id: string
  pillar: RunPillar | string
  status: RunStatus
  created_at: string
  idea_text?: string
}

export interface Meta {
  request_id: string
  timestamp: string
}

export interface ResponseEnvelope<T> {
  data: T
  meta: Meta
}

export interface PaginationInfo {
  cursor: string | null
  has_more: boolean
  total: number
}

export interface PaginatedResponseEnvelope<T> {
  data: T[]
  pagination: PaginationInfo
  meta: Meta
}

export interface IdeaCreate {
  text: string
}

export type GateState = 'pending' | 'approved' | 'rejected'

export interface Gate {
  id: string
  run_id: string
  state: GateState
  pillar: string
  decided_by?: string
  decided_at?: string
}

export interface GateDecision {
  decision: 'approved' | 'rejected'
  notes?: string
}

export interface GateRead extends Gate {
  created_at: string
}

export interface User {
  id: string
  email: string
  name?: string
  role?: 'founder' | 'admin' | 'superadmin'
  avatar_url?: string
  organization_id?: string
}

// ------------------------------------------------------------------
// UI-layer mock / enriched types
// ------------------------------------------------------------------

export interface LeanCanvasSection {
  title: string
  content: string[]
}

export interface Persona {
  name: string
  role: string
  pain_points: string[]
  goals: string[]
}

export interface StrategyOutput {
  viability_score: number
  lean_canvas: LeanCanvasSection[]
  personas: Persona[]
  recommendation: 'proceed' | 'pivot' | 'abandon'
}

export interface StackCard {
  layer: string
  technology: string
  rationale: string
}

export interface ArchitectureOutput {
  diagram_mermaid: string
  stack: StackCard[]
  openapi_summary: { path: string; method: string; summary: string }[]
}

export interface FileNode {
  name: string
  type: 'file' | 'directory'
  language?: string
  content?: string
  children?: FileNode[]
}

export interface TestResult {
  name: string
  status: 'pass' | 'fail' | 'skip'
  duration_ms: number
  message?: string
}

export interface SecurityFinding {
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  title: string
  file?: string
  line?: number
}

export interface ReviewOutput {
  overall: 'APPROVED' | 'ESCALATE'
  test_results: TestResult[]
  coverage_pct: number
  security_findings: SecurityFinding[]
  self_heal_iterations: number
}

export interface DeployOutput {
  live_url?: string
  status: 'deploying' | 'live' | 'failed'
  deploy_log: string[]
  monthly_cost_usd: number
}

export interface MarketingOutput {
  landing_url?: string
  gtm_summary: string
  social_posts: { platform: string; copy: string; scheduled_at: string }[]
}

export interface TenantRow {
  id: string
  name: string
  plan: string
  runs_count: number
  tokens_used: number
  status: 'active' | 'suspended'
}
