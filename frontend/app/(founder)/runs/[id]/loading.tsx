import { Skeleton } from '@/components/ui/skeleton'

export default function RunDetailLoading() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Skeleton className="h-8 w-8 rounded-md" />
        <Skeleton className="h-6 w-64" />
      </div>
      <Skeleton className="h-12 w-full rounded-xl" />
      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-24 rounded-xl" />
    </div>
  )
}
