'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, ArrowRight, CheckCircle2, Loader2, Lightbulb, Tag } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { createIdea } from '@/lib/api-client'
import { cn, truncate } from '@/lib/utils'

const STEPS = ['Describe Your Idea', 'Select Domain', 'Review & Submit']

const DOMAINS = [
  { value: 'fintech', label: 'FinTech', emoji: '💳' },
  { value: 'healthtech', label: 'HealthTech', emoji: '🏥' },
  { value: 'agritech', label: 'AgriTech', emoji: '🌾' },
  { value: 'edtech', label: 'EdTech', emoji: '📚' },
  { value: 'hrtech', label: 'HR Tech', emoji: '👥' },
  { value: 'legaltech', label: 'LegalTech', emoji: '⚖️' },
  { value: 'ecommerce', label: 'E-Commerce', emoji: '🛒' },
  { value: 'logistics', label: 'Logistics', emoji: '🚚' },
  { value: 'proptech', label: 'PropTech', emoji: '🏠' },
  { value: 'saas', label: 'B2B SaaS', emoji: '⚙️' },
  { value: 'ai', label: 'AI / ML Tools', emoji: '🤖' },
  { value: 'other', label: 'Other', emoji: '✨' },
]

const EXAMPLE_IDEAS = [
  'AI-powered invoice automation for Indian SMBs — auto-reconcile GST, send WhatsApp reminders, integrate with Tally.',
  'Real-time crop disease detection via drone imagery + AI alerts for farmers in regional languages.',
  'B2B SaaS for hostel & PG management — tenant onboarding, rent collection, maintenance ticketing.',
]

export default function NewIdeaPage() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [ideaText, setIdeaText] = useState('')
  const [domain, setDomain] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function canProceedStep0() {
    return ideaText.trim().length >= 10
  }

  function canProceedStep1() {
    return domain !== null
  }

  async function handleSubmit() {
    setLoading(true)
    setError(null)
    try {
      const result = await createIdea({ text: ideaText.trim() })
      router.push(`/runs/${result.data.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit idea. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col">
      <Header title="New Idea" />
      <div className="flex-1 p-6">
        {/* Stepper */}
        <div className="mb-8 flex items-center gap-2">
          {STEPS.map((label, idx) => (
            <div key={label} className="flex flex-1 items-center">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-colors',
                    idx < step
                      ? 'bg-primary text-white'
                      : idx === step
                      ? 'bg-primary text-white ring-4 ring-primary/20'
                      : 'bg-muted text-muted-foreground'
                  )}
                >
                  {idx < step ? <CheckCircle2 className="h-4 w-4" /> : idx + 1}
                </div>
                <span
                  className={cn(
                    'mt-1 hidden text-[10px] font-medium sm:block',
                    idx === step ? 'text-primary' : 'text-muted-foreground'
                  )}
                >
                  {label}
                </span>
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={cn(
                    'mx-2 h-0.5 flex-1 transition-colors',
                    idx < step ? 'bg-primary' : 'bg-muted'
                  )}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step 0: Idea */}
        {step === 0 && (
          <Card className="mx-auto max-w-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-primary" />
                Describe Your Startup Idea
              </CardTitle>
              <CardDescription>
                Be specific. Include the problem, target customer, and how your product solves it.
                Minimum 10 characters, max 10,000.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="idea-text">Your Idea</Label>
                <Textarea
                  id="idea-text"
                  value={ideaText}
                  onChange={(e) => setIdeaText(e.target.value)}
                  placeholder="e.g. An AI-powered SaaS that automates GST filing for Indian SMBs..."
                  rows={6}
                  maxLength={10000}
                  className="resize-none"
                />
                <p className="text-right text-xs text-muted-foreground">
                  {ideaText.length} / 10,000
                </p>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Try an example
                </p>
                {EXAMPLE_IDEAS.map((ex, i) => (
                  <button
                    key={i}
                    type="button"
                    className="block w-full rounded-md border border-dashed px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-foreground"
                    onClick={() => setIdeaText(ex)}
                  >
                    {ex}
                  </button>
                ))}
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={() => setStep(1)}
                  disabled={!canProceedStep0()}
                  className="gap-1.5"
                >
                  Next <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 1: Domain */}
        {step === 1 && (
          <Card className="mx-auto max-w-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Tag className="h-5 w-5 text-primary" />
                Select Domain
              </CardTitle>
              <CardDescription>
                Choose the primary domain. This helps the Strategy agent focus competitive research.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {DOMAINS.map((d) => (
                  <button
                    key={d.value}
                    type="button"
                    onClick={() => setDomain(d.value)}
                    className={cn(
                      'flex items-center gap-2 rounded-lg border-2 px-3 py-2.5 text-left text-sm font-medium transition-all',
                      domain === d.value
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border hover:border-primary/40 hover:bg-muted/50'
                    )}
                  >
                    <span>{d.emoji}</span>
                    <span>{d.label}</span>
                  </button>
                ))}
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setStep(0)} className="gap-1.5">
                  <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <Button
                  onClick={() => setStep(2)}
                  disabled={!canProceedStep1()}
                  className="gap-1.5"
                >
                  Next <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Review */}
        {step === 2 && (
          <Card className="mx-auto max-w-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-primary" />
                Review &amp; Submit
              </CardTitle>
              <CardDescription>
                AutoFounder will run 7 autonomous pillars: Strategy, Research, Product Plan,
                Engineering, QA Review, DevOps, and Marketing.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Idea
                  </p>
                  <p className="mt-1 text-sm">{truncate(ideaText, 300)}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Domain
                  </p>
                  <Badge variant="secondary" className="mt-1">
                    {DOMAINS.find((d) => d.value === domain)?.emoji}{' '}
                    {DOMAINS.find((d) => d.value === domain)?.label ?? domain}
                  </Badge>
                </div>
              </div>

              <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm text-primary">
                <strong>What happens next:</strong> AutoFounder AI will create a run, validate
                market viability, design the architecture, write code, run tests, deploy to AWS,
                and generate a GTM plan — all autonomously. Estimated time: 10–30 minutes.
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setStep(1)} className="gap-1.5">
                  <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <Button onClick={handleSubmit} disabled={loading} className="gap-1.5">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  {loading ? 'Launching...' : 'Launch Run'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
