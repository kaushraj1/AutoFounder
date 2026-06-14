import { cn } from '@/lib/utils'
import { CheckCircle2, Circle, Loader2 } from 'lucide-react'

const PILLARS = [
  { key: 'strategy', label: 'Strategy' },
  { key: 'research', label: 'Research' },
  { key: 'product_planner', label: 'Product Plan' },
  { key: 'engineering', label: 'Engineering' },
  { key: 'review', label: 'QA Review' },
  { key: 'devops', label: 'DevOps' },
  { key: 'marketing', label: 'Marketing' },
]

const PILLAR_ORDER: Record<string, number> = {
  strategy: 0,
  research: 1,
  product_planner: 2,
  engineering: 3,
  review: 4,
  devops: 5,
  marketing: 6,
  '1': 0,
  '2': 1,
  '3': 2,
  '4': 3,
  '5': 4,
  '6': 5,
  '7': 6,
}

interface PillarProgressProps {
  currentPillar: string
  status: string
  className?: string
}

export function PillarProgress({ currentPillar, status, className }: PillarProgressProps) {
  const currentIdx = PILLAR_ORDER[currentPillar] ?? 0
  const isCompleted = status === 'completed'

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between">
        {PILLARS.map((pillar, idx) => {
          const isDone = isCompleted || idx < currentIdx
          const isCurrent = !isCompleted && idx === currentIdx
          const isUpcoming = !isCompleted && idx > currentIdx

          return (
            <div key={pillar.key} className="flex flex-1 flex-col items-center">
              <div className="flex w-full items-center">
                {idx > 0 && (
                  <div
                    className={cn(
                      'h-0.5 flex-1 transition-colors',
                      isDone ? 'bg-primary' : 'bg-muted'
                    )}
                  />
                )}
                <div className="flex flex-col items-center">
                  {isDone ? (
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                  ) : isCurrent ? (
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  ) : (
                    <Circle className={cn('h-5 w-5', isUpcoming ? 'text-muted-foreground' : 'text-primary')} />
                  )}
                </div>
                {idx < PILLARS.length - 1 && (
                  <div
                    className={cn(
                      'h-0.5 flex-1 transition-colors',
                      isDone ? 'bg-primary' : 'bg-muted'
                    )}
                  />
                )}
              </div>
              <span
                className={cn(
                  'mt-1 hidden text-[10px] font-medium sm:block',
                  isCurrent
                    ? 'text-primary'
                    : isDone
                    ? 'text-muted-foreground'
                    : 'text-muted-foreground/50'
                )}
              >
                {pillar.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
