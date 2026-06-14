'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, TrendingUp, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ApprovalGate } from '@/components/hitl/ApprovalGate'
import { Header } from '@/components/layout/Header'
import { MOCK_STRATEGY } from '@/lib/mock-data'
import { cn } from '@/lib/utils'

const CANVAS_COLORS: Record<string, string> = {
  Problem: 'border-l-red-400',
  Solution: 'border-l-blue-400',
  'Unique Value Proposition': 'border-l-purple-400',
  'Unfair Advantage': 'border-l-yellow-400',
  'Customer Segments': 'border-l-green-400',
  'Key Metrics': 'border-l-cyan-400',
  Channels: 'border-l-orange-400',
  'Cost Structure': 'border-l-rose-400',
  'Revenue Streams': 'border-l-emerald-400',
}

export default function StrategyPage() {
  const { id } = useParams<{ id: string }>()
  const strategy = MOCK_STRATEGY

  const viabilityColor =
    strategy.viability_score >= 75
      ? 'text-green-700'
      : strategy.viability_score >= 50
      ? 'text-yellow-700'
      : 'text-red-700'

  return (
    <div className="flex flex-col">
      <Header title="Strategy Output" />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="icon" className="h-8 w-8">
            <Link href={`/runs/${id}`}><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <h2 className="text-base font-semibold">Strategy &amp; Viability Analysis</h2>
        </div>

        {/* HITL Gate */}
        <ApprovalGate
          runId={id}
          gateId="gate-strategy-001"
          pillarName="Strategy"
          onDecision={(decision) => console.log('Gate decision:', decision)}
        />

        {/* Viability Score */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="h-4 w-4 text-primary" />
              Viability Score
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-end gap-3">
              <span className={cn('text-4xl font-bold', viabilityColor)}>
                {strategy.viability_score}
              </span>
              <span className="mb-1 text-muted-foreground">/ 100</span>
              <Badge
                variant={strategy.recommendation === 'proceed' ? 'success' : strategy.recommendation === 'pivot' ? 'warning' : 'destructive'}
                className="mb-1 ml-auto"
              >
                {strategy.recommendation === 'proceed'
                  ? 'Recommended: Proceed'
                  : strategy.recommendation === 'pivot'
                  ? 'Recommended: Pivot'
                  : 'Recommended: Abandon'}
              </Badge>
            </div>
            <Progress value={strategy.viability_score} className="h-3" />
            <p className="text-xs text-muted-foreground">
              Composite score across market size, competitive landscape, technical feasibility, and team-market fit.
            </p>
          </CardContent>
        </Card>

        {/* Lean Canvas */}
        <div>
          <h3 className="mb-3 text-sm font-semibold">Lean Canvas</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {strategy.lean_canvas.map((section) => (
              <Card
                key={section.title}
                className={cn('border-l-4', CANVAS_COLORS[section.title] ?? 'border-l-gray-300')}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{section.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {section.content.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary/60" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Personas */}
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Users className="h-4 w-4 text-primary" />
            Ideal Customer Profiles
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {strategy.personas.map((persona) => (
              <Card key={persona.name}>
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-lg font-bold text-primary">
                      {persona.name.charAt(0)}
                    </div>
                    <div>
                      <CardTitle className="text-sm">{persona.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">{persona.role}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-red-600">Pain Points</p>
                    <ul className="space-y-1">
                      {persona.pain_points.map((p, i) => (
                        <li key={i} className="text-xs text-muted-foreground">• {p}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-green-600">Goals</p>
                    <ul className="space-y-1">
                      {persona.goals.map((g, i) => (
                        <li key={i} className="text-xs text-muted-foreground">• {g}</li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
