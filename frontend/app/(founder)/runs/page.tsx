'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { Plus, RefreshCw } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { RunCard } from '@/components/runs/RunCard'
import { listRuns } from '@/lib/api-client'
import { MOCK_RUNS } from '@/lib/mock-data'
import type { Run } from '@/lib/types'

export default function RunsPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['runs', 'all'],
    queryFn: () => listRuns({ limit: 50 }),
  })

  const runs: Run[] = data?.data ?? MOCK_RUNS

  return (
    <div className="flex flex-col">
      <Header title="All Runs" />
      <div className="flex-1 space-y-4 p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {runs.length} run{runs.length !== 1 ? 's' : ''} total
          </p>
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

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-36 w-full rounded-xl" />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {runs.map((run) => (
              <RunCard key={run.id} run={run} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
