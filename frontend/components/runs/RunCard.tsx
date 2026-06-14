import Link from 'next/link'
import { ArrowRight, Calendar, Cpu } from 'lucide-react'
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StatusBadge } from './StatusBadge'
import { PillarProgress } from './PillarProgress'
import type { Run } from '@/lib/types'
import { formatRelative, pillarLabel, truncate } from '@/lib/utils'

interface RunCardProps {
  run: Run
}

export function RunCard({ run }: RunCardProps) {
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium leading-snug text-foreground">
              {run.idea_text ? truncate(run.idea_text, 100) : `Run ${run.id.slice(0, 8)}`}
            </p>
          </div>
          <StatusBadge status={run.status} />
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <PillarProgress currentPillar={run.pillar} status={run.status} />
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0 text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Cpu className="h-3 w-3" />
            {pillarLabel(run.pillar)}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatRelative(run.created_at)}
          </span>
        </div>
        <Button asChild size="sm" variant="ghost" className="h-7 px-2 text-xs">
          <Link href={`/runs/${run.id}`}>
            View <ArrowRight className="ml-1 h-3 w-3" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
