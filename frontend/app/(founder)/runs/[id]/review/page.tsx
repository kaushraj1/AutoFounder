'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, CheckCircle2, XCircle, MinusCircle, ShieldAlert, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Header } from '@/components/layout/Header'
import { MOCK_REVIEW } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import type { SecurityFinding, TestResult } from '@/lib/types'

const SEVERITY_COLORS: Record<SecurityFinding['severity'], string> = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
  info: 'bg-gray-100 text-gray-700 border-gray-200',
}

function TestRow({ t }: { t: TestResult }) {
  return (
    <tr className="border-b last:border-0 hover:bg-muted/30">
      <td className="px-4 py-2.5">
        {t.status === 'pass' ? (
          <CheckCircle2 className="h-4 w-4 text-green-600" />
        ) : t.status === 'fail' ? (
          <XCircle className="h-4 w-4 text-red-600" />
        ) : (
          <MinusCircle className="h-4 w-4 text-gray-400" />
        )}
      </td>
      <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">{t.name}</td>
      <td className="px-4 py-2.5">
        <Badge
          variant={t.status === 'pass' ? 'success' : t.status === 'fail' ? 'destructive' : 'secondary'}
          className="text-xs"
        >
          {t.status}
        </Badge>
      </td>
      <td className="px-4 py-2.5 text-right text-xs text-muted-foreground">{t.duration_ms}ms</td>
      <td className="px-4 py-2.5 text-xs text-muted-foreground">{t.message ?? '—'}</td>
    </tr>
  )
}

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>()
  const review = MOCK_REVIEW

  const passCount = review.test_results.filter((t) => t.status === 'pass').length
  const failCount = review.test_results.filter((t) => t.status === 'fail').length
  const skipCount = review.test_results.filter((t) => t.status === 'skip').length

  return (
    <div className="flex flex-col">
      <Header title="QA Review" />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="icon" className="h-8 w-8">
            <Link href={`/runs/${id}`}><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <h2 className="text-base font-semibold">QA Review Results</h2>
          <Badge
            variant={review.overall === 'APPROVED' ? 'success' : 'warning'}
            className="ml-auto"
          >
            {review.overall === 'APPROVED' ? '✓ APPROVED' : '⚠ ESCALATE'}
          </Badge>
        </div>

        {/* Summary cards */}
        <div className="grid gap-4 sm:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Tests Passed</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">{passCount}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Tests Failed</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={cn('text-2xl font-bold', failCount > 0 ? 'text-red-600' : 'text-muted-foreground')}>
                {failCount}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Coverage</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1.5">
              <p className="text-2xl font-bold">{review.coverage_pct}%</p>
              <Progress value={review.coverage_pct} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <RefreshCw className="h-3 w-3" />
                Self-Heal Iterations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{review.self_heal_iterations}</p>
            </CardContent>
          </Card>
        </div>

        {/* Test Results table */}
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            Test Results
            <Badge variant="secondary">{review.test_results.length} total</Badge>
            <Badge variant="success" className="ml-1">{passCount} pass</Badge>
            {failCount > 0 && <Badge variant="destructive">{failCount} fail</Badge>}
            {skipCount > 0 && <Badge variant="secondary">{skipCount} skip</Badge>}
          </h3>
          <div className="overflow-hidden rounded-xl border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="w-10 px-4 py-2.5" />
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Test Name
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Status
                  </th>
                  <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Duration
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Message
                  </th>
                </tr>
              </thead>
              <tbody>
                {review.test_results.map((t) => (
                  <TestRow key={t.name} t={t} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Security Findings */}
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <ShieldAlert className="h-4 w-4 text-orange-500" />
            Security Findings
            <Badge variant="secondary">{review.security_findings.length}</Badge>
          </h3>
          {review.security_findings.length === 0 ? (
            <p className="text-sm text-green-600">No security findings — clean scan.</p>
          ) : (
            <div className="space-y-2">
              {review.security_findings.map((f, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex items-start gap-3 rounded-lg border px-4 py-3',
                    SEVERITY_COLORS[f.severity]
                  )}
                >
                  <Badge className={cn('mt-0.5 flex-shrink-0 text-[10px]', SEVERITY_COLORS[f.severity])}>
                    {f.severity.toUpperCase()}
                  </Badge>
                  <div>
                    <p className="text-sm font-medium">{f.title}</p>
                    {f.file && (
                      <p className="mt-0.5 font-mono text-xs opacity-70">
                        {f.file}{f.line ? `:${f.line}` : ''}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
