import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
      <p className="text-6xl font-black text-primary">404</p>
      <div>
        <h2 className="text-lg font-semibold">Page not found</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          This page does not exist or has been moved.
        </p>
      </div>
      <Button asChild>
        <Link href="/dashboard">Back to Dashboard</Link>
      </Button>
    </div>
  )
}
