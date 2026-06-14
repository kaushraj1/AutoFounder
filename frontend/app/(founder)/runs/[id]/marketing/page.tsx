'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Download, ExternalLink, Megaphone, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Header } from '@/components/layout/Header'
import { MOCK_MARKETING } from '@/lib/mock-data'
import { formatDate } from '@/lib/utils'

const PLATFORM_COLORS: Record<string, string> = {
  'LinkedIn': 'bg-blue-100 text-blue-800',
  'Twitter/X': 'bg-slate-100 text-slate-800',
  'WhatsApp Broadcast': 'bg-green-100 text-green-800',
}

export default function MarketingPage() {
  const { id } = useParams<{ id: string }>()
  const marketing = MOCK_MARKETING

  return (
    <div className="flex flex-col">
      <Header title="Marketing" />
      <div className="flex-1 space-y-6 p-6">
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="icon" className="h-8 w-8">
            <Link href={`/runs/${id}`}><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <h2 className="text-base font-semibold">GTM &amp; Marketing Plan</h2>
        </div>

        {/* Landing page preview */}
        {marketing.landing_url && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                Landing Page
                <a
                  href={marketing.landing_url}
                  target="_blank"
                  rel="noreferrer"
                  className="ml-auto flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  Open <ExternalLink className="h-3 w-3" />
                </a>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-hidden rounded-lg border bg-muted/30" style={{ height: '180px' }}>
                <div className="flex h-full items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto mb-3 h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <Megaphone className="h-6 w-6 text-primary" />
                    </div>
                    <p className="text-sm font-medium">Landing Page Preview</p>
                    <a
                      href={marketing.landing_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 flex items-center justify-center gap-1 text-xs text-primary hover:underline"
                    >
                      {marketing.landing_url}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* GTM Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Go-To-Market Strategy</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-muted-foreground">{marketing.gtm_summary}</p>
          </CardContent>
        </Card>

        {/* Social Post Calendar */}
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Calendar className="h-4 w-4 text-primary" />
            Launch Post Calendar
          </h3>
          <div className="space-y-3">
            {marketing.social_posts.map((post, i) => (
              <Card key={i}>
                <CardContent className="pt-4">
                  <div className="flex items-start gap-3">
                    <Badge
                      className={PLATFORM_COLORS[post.platform] ?? 'bg-gray-100 text-gray-700'}
                    >
                      {post.platform}
                    </Badge>
                    <div className="flex-1">
                      <p className="text-sm">{post.copy}</p>
                      <p className="mt-1.5 text-xs text-muted-foreground">
                        Scheduled: {formatDate(post.scheduled_at)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button className="gap-1.5">
            <Download className="h-4 w-4" />
            Download Launch Kit
          </Button>
          <Button variant="outline" className="gap-1.5">
            <Calendar className="h-4 w-4" />
            Export to Notion
          </Button>
        </div>
      </div>
    </div>
  )
}
