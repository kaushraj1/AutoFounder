'use client'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { StatusBadge } from '@/components/runs/StatusBadge'
import { PillarProgress } from '@/components/runs/PillarProgress'
import { ApprovalGate } from '@/components/hitl/ApprovalGate'
import { getRun, listGates } from '@/lib/api-client'
import { MOCK_RUNS } from '@/lib/mock-data'
import { formatDate, pillarLabel } from '@/lib/utils'
import type { Run } from '@/lib/types'

const PILLAR_TABS = [
  { key: 'strategy', label: 'Strategy', href: 'strategy' },
  { key: 'research', label: 'Research', href: 'strategy' },
  { key: 'product_planner', label: 'Product Plan', href: 'strategy' },
  { key: 'architecture', label: 'Architecture', href: 'architecture' },
  { key: 'engineering', label: 'Code', href: 'code' },
  { key: 'review', label: 'QA Review', href: 'review' },
  { key: 'devops', label: 'Deploy', href: 'deploy' },
  { key: 'marketing', label: 'Marketing', href: 'marketing' },
]

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['run', id],
    queryFn: () => getRun(id),
    refetchInterval: 15_000,
  })

  const run: Run = data?.data ?? MOCK_RUNS.find((r) => r.id === id) ?? MOCK_RUNS[0]

  const needsReview = run.status === 'paused' || run.status === 'awaiting_review'

  const { data: gatesData } = useQuery({
    queryKey: ['gates', id],
    queryFn: () => listGates(id),
    enabled: needsReview,
    refetchInterval: needsReview ? 5_000 : false,
  })

  const pendingGate = gatesData?.data?.find((g) => g.state === 'pending')

  return (
    <div className="flex flex-col">
      <Header />
      <div className="flex-1 space-y-6 p-6">
        {/* Back + title */}
        <div className="flex items-center gap-3">
          <Button asChild variant="ghost" size="icon" className="h-8 w-8">
            <Link href="/dashboard">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          {isLoading ? (
            <Skeleton className="h-5 w-48" />
          ) : (
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-semibold truncate">
                  {run.idea_text
                    ? run.idea_text.slice(0, 80) + (run.idea_text.length > 80 ? '…' : '')
                    : `Run ${run.id.slice(0, 8)}`}
                </h2>
                <StatusBadge status={run.status} />
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Started {formatDate(run.created_at)} · Pillar: {pillarLabel(run.pillar)}
              </p>
            </div>
          )}
        </div>

        {/* Pillar progress bar */}
        {!isLoading && (
          <PillarProgress currentPillar={run.pillar} status={run.status} />
        )}

        {/* HITL Approval Gate — shown when run is awaiting human review */}
        {needsReview && pendingGate && (
          <ApprovalGate
            runId={id}
            gateId={pendingGate.id}
            pillarName={
              {
                validation_approve: 'Strategy',
                architecture_approve: 'Architecture',
                infra_spend_approve: 'DevOps',
                launch_approve: 'Marketing',
              }[pendingGate.kind] ?? pillarLabel(run.pillar)
            }
            onDecision={() => {
              queryClient.invalidateQueries({ queryKey: ['run', id] })
              queryClient.invalidateQueries({ queryKey: ['gates', id] })
            }}
          />
        )}

        {/* Awaiting review but no gate record yet — dev mode fallback */}
        {needsReview && !pendingGate && (
          <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 text-orange-500 text-xl">⏳</span>
              <div>
                <p className="font-medium text-orange-900">Awaiting Review</p>
                <p className="mt-0.5 text-sm text-orange-700">
                  The <strong>{pillarLabel(run.pillar)}</strong> pillar output is being prepared for review.
                  The approval gate will appear here once the pillar output is ready.
                </p>
                <p className="mt-2 text-xs text-orange-600">
                  This page auto-refreshes every 5 seconds.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation to sub-pages */}
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
          {[
            { href: `/runs/${id}/strategy`, label: 'Strategy', emoji: '🎯' },
            { href: `/runs/${id}/architecture`, label: 'Architecture', emoji: '🏗️' },
            { href: `/runs/${id}/code`, label: 'Code', emoji: '💻' },
            { href: `/runs/${id}/review`, label: 'QA Review', emoji: '🧪' },
            { href: `/runs/${id}/deploy`, label: 'Deploy', emoji: '🚀' },
            { href: `/runs/${id}/marketing`, label: 'Marketing', emoji: '📣' },
          ].map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              className="flex flex-col items-center justify-center gap-1.5 rounded-xl border bg-card p-4 text-sm font-medium transition-all hover:border-primary/40 hover:bg-primary/5 hover:text-primary"
            >
              <span className="text-2xl">{tab.emoji}</span>
              <span>{tab.label}</span>
              <ExternalLink className="h-3 w-3 text-muted-foreground" />
            </Link>
          ))}
        </div>

        {/* Run metadata */}
        <div className="rounded-xl border bg-muted/30 p-4">
          <dl className="grid gap-3 sm:grid-cols-3">
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Run ID</dt>
              <dd className="mt-0.5 font-mono text-xs text-foreground">{run.id}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</dt>
              <dd className="mt-0.5">
                <StatusBadge status={run.status} />
              </dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Current Pillar</dt>
              <dd className="mt-0.5 text-sm">{pillarLabel(run.pillar)}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
