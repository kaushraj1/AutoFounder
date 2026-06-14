'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  Plus,
  Rocket,
  Globe,
  Zap,
  TrendingUp,
  RefreshCw,
} from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { RunCard } from '@/components/runs/RunCard'
import { listRuns } from '@/lib/api-client'
import { MOCK_RUNS } from '@/lib/mock-data'
import type { Run } from '@/lib/types'

function StatCard({
  title,
  value,
  sub,
  icon: Icon,
  color,
}: {
  title: string
  value: string | number
  sub?: string
  icon: React.ElementType
  color: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={`rounded-md p-1.5 ${color}`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
        {sub && <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['runs'],
    queryFn: () => listRuns({ limit: 10 }),
    // Fall back gracefully when API is unavailable
  })

  const runs: Run[] = data?.data ?? MOCK_RUNS
  const total = data?.pagination?.total ?? MOCK_RUNS.length
  const liveCount = runs.filter((r) => r.status === 'completed').length
  const runningCount = runs.filter((r) => r.status === 'running').length

  return (
    <div className="flex flex-col">
      <Header title="Dashboard" />

      <div className="flex-1 space-y-6 p-6">
        {/* Hero CTA */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Welcome back, Founder</h2>
            <p className="text-sm text-muted-foreground">
              {runningCount > 0
                ? `${runningCount} run${runningCount > 1 ? 's' : ''} in progress right now.`
                : 'Ready to build your next AI-validated startup?'}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-1.5">
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
            <Button asChild size="sm" className="gap-1.5">
              <Link href="/ideas/new">
                <Plus className="h-4 w-4" />
                New Idea
              </Link>
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Runs"
            value={total}
            sub="All time"
            icon={Rocket}
            color="bg-blue-100 text-blue-700"
          />
          <StatCard
            title="Live Products"
            value={liveCount}
            sub="Deployed & validated"
            icon={Globe}
            color="bg-green-100 text-green-700"
          />
          <StatCard
            title="Active Runs"
            value={runningCount}
            sub="Running right now"
            icon={Zap}
            color="bg-yellow-100 text-yellow-700"
          />
          <StatCard
            title="Tokens Today"
            value="284k"
            sub="~$0.85 spend"
            icon={TrendingUp}
            color="bg-purple-100 text-purple-700"
          />
        </div>

        {/* Runs list */}
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Recent Runs</h3>
            <Button asChild variant="link" size="sm" className="h-auto p-0 text-xs">
              <Link href="/runs">View all</Link>
            </Button>
          </div>

          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-36 w-full rounded-xl" />
              ))}
            </div>
          ) : isError && runs.length === 0 ? (
            <div className="rounded-xl border border-dashed p-10 text-center">
              <p className="text-sm text-muted-foreground">
                Could not load runs. Check your API connection.
              </p>
            </div>
          ) : runs.length === 0 ? (
            <div className="rounded-xl border border-dashed p-10 text-center">
              <Rocket className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium">No runs yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Submit your first idea to start the AI validation pipeline.
              </p>
              <Button asChild className="mt-4 gap-1.5" size="sm">
                <Link href="/ideas/new">
                  <Plus className="h-3.5 w-3.5" />
                  New Idea
                </Link>
              </Button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {runs.map((run) => (
                <RunCard key={run.id} run={run} />
              ))}
            </div>
          )}
        </div>

        {/* Quick tips */}
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex items-start gap-3 pt-4">
            <Zap className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
            <div>
              <p className="text-sm font-medium">Pro tip: Human-in-the-loop gates</p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                AutoFounder pauses at key decision points — Strategy, Architecture, and Code Review —
                for your approval before proceeding. You stay in control at every step.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
