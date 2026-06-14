'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, ExternalLink, DollarSign, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Header } from '@/components/layout/Header'
import { MOCK_DEPLOY } from '@/lib/mock-data'

export default function DeployPage() {
  const { id } = useParams<{ id: string }>()
  const deploy = MOCK_DEPLOY

  return (
    <div className="flex flex-col">
      <Header title="Deployment" />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="icon" className="h-8 w-8">
            <Link href={`/runs/${id}`}><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <h2 className="text-base font-semibold">Deployment Status</h2>
        </div>

        {/* Status banner */}
        <div
          className={
            deploy.status === 'live'
              ? 'rounded-xl border border-green-200 bg-green-50 p-4'
              : deploy.status === 'failed'
              ? 'rounded-xl border border-red-200 bg-red-50 p-4'
              : 'rounded-xl border border-blue-200 bg-blue-50 p-4'
          }
        >
          <div className="flex items-center gap-3">
            {deploy.status === 'live' ? (
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            ) : deploy.status === 'failed' ? (
              <XCircle className="h-6 w-6 text-red-600" />
            ) : (
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            )}
            <div>
              <p className="font-semibold">
                {deploy.status === 'live'
                  ? 'Your app is live!'
                  : deploy.status === 'failed'
                  ? 'Deployment failed'
                  : 'Deploying to AWS ECS Fargate...'}
              </p>
              {deploy.live_url && (
                <a
                  href={deploy.live_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-0.5 flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  {deploy.live_url}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
            <Badge variant={deploy.status === 'live' ? 'success' : deploy.status === 'failed' ? 'destructive' : 'info'} className="ml-auto capitalize">
              {deploy.status}
            </Badge>
          </div>
        </div>

        {/* Stats */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Live URL</CardTitle>
            </CardHeader>
            <CardContent>
              {deploy.live_url ? (
                <a
                  href={deploy.live_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                >
                  {deploy.live_url.replace('https://', '')}
                  <ExternalLink className="h-3 w-3" />
                </a>
              ) : (
                <span className="text-sm text-muted-foreground">Pending…</span>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <DollarSign className="h-3.5 w-3.5" />
                Est. Monthly Cost
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">${deploy.monthly_cost_usd.toFixed(2)}</p>
              <p className="text-xs text-muted-foreground">AWS ECS Fargate + RDS + S3</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Infrastructure</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {['ECS Fargate', 'RDS PostgreSQL', 'ElastiCache', 'S3', 'ALB'].map((svc) => (
                  <Badge key={svc} variant="secondary" className="text-xs">
                    {svc}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Deploy log */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">CI/CD Deploy Log</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto rounded-lg bg-slate-950 p-4" style={{ maxHeight: '300px' }}>
              {deploy.deploy_log.map((line, i) => (
                <p key={i} className="font-mono text-xs leading-relaxed text-slate-300">
                  {line}
                </p>
              ))}
              {deploy.status === 'deploying' && (
                <p className="mt-1 animate-pulse font-mono text-xs text-slate-400">
                  ▌ Waiting for health check...
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        {deploy.live_url && (
          <div className="flex gap-2">
            <Button asChild className="gap-1.5">
              <a href={deploy.live_url} target="_blank" rel="noreferrer">
                <ExternalLink className="h-4 w-4" />
                Open Live App
              </a>
            </Button>
            <Button variant="outline" className="gap-1.5">
              View CloudWatch Logs
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
