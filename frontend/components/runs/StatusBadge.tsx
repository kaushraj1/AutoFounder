import type { RunStatus } from '@/lib/types'
import { cn, statusColor } from '@/lib/utils'

interface StatusBadgeProps {
  status: RunStatus
  className?: string
}

const STATUS_LABELS: Record<RunStatus, string> = {
  queued: 'Queued',
  running: 'Running',
  paused: 'Awaiting Review',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold',
        statusColor(status),
        className
      )}
    >
      {status === 'running' && (
        <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-blue-600" />
      )}
      {STATUS_LABELS[status]}
    </span>
  )
}
