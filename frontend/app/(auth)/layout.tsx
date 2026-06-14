import type { Metadata } from 'next'
import { Zap } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Sign In',
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-primary/5 via-background to-secondary/20 px-4">
      <div className="mb-8 flex flex-col items-center gap-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg">
          <Zap className="h-6 w-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight">AutoFounder AI</h1>
        <p className="text-sm text-muted-foreground">A true AI co-founder that gets things done.</p>
      </div>
      {children}
    </div>
  )
}
