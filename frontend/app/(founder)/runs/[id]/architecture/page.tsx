'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Layers, Code2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Header } from '@/components/layout/Header'
import { MOCK_ARCHITECTURE } from '@/lib/mock-data'

export default function ArchitecturePage() {
  const { id } = useParams<{ id: string }>()
  const arch = MOCK_ARCHITECTURE

  return (
    <div className="flex flex-col">
      <Header title="Architecture Output" />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="icon" className="h-8 w-8">
            <Link href={`/runs/${id}`}><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <h2 className="text-base font-semibold">System Architecture</h2>
        </div>

        {/* Mermaid diagram (rendered as pre for now; can add mermaid.js in client component) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">System Diagram</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto rounded-lg bg-slate-950 p-4">
              <pre className="font-mono text-xs leading-relaxed text-slate-200">
                {arch.diagram_mermaid}
              </pre>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Mermaid graph — paste into{' '}
              <a
                href="https://mermaid.live"
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                mermaid.live
              </a>{' '}
              to render interactively.
            </p>
          </CardContent>
        </Card>

        {/* Tech Stack */}
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Layers className="h-4 w-4 text-primary" />
            Technology Stack
          </h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {arch.stack.map((card) => (
              <Card key={card.layer}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">{card.layer}</CardTitle>
                    <Badge variant="secondary" className="text-xs">
                      {card.technology.split(' ')[0]}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs font-medium text-foreground">{card.technology}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{card.rationale}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* OpenAPI Summary */}
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Code2 className="h-4 w-4 text-primary" />
            API Endpoints
          </h3>
          <div className="overflow-hidden rounded-xl border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Method
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Path
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Summary
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {arch.openapi_summary.map((ep, i) => (
                  <tr key={i} className="hover:bg-muted/30">
                    <td className="px-4 py-2.5">
                      <Badge
                        variant={ep.method === 'POST' ? 'info' : ep.method === 'DELETE' ? 'destructive' : 'secondary'}
                        className="font-mono text-xs"
                      >
                        {ep.method}
                      </Badge>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                      {ep.path}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground">{ep.summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
