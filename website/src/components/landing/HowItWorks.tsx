import { ArrowRight, FileText, Layers, Rocket } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Step {
  number: string
  icon: LucideIcon
  title: string
  description: string
}

const steps: Step[] = [
  {
    number: '01',
    icon: FileText,
    title: 'Submit Your Idea',
    description:
      'Type your startup idea in plain English. Attach a PDF, voice note, or URL for extra context. AutoFounder AI understands text, images, audio, and documents.',
  },
  {
    number: '02',
    icon: Layers,
    title: 'AI Builds in Parallel',
    description:
      'Specialized agents handle validation, architecture, code, testing, deployment, and marketing simultaneously. You review and approve at 4 key checkpoints.',
  },
  {
    number: '03',
    icon: Rocket,
    title: 'Launch & Keep Improving',
    description:
      'Your MVP goes live with a full marketing kit. The LLMOps agent continuously learns from user feedback, optimises your product, and tracks costs — week after week.',
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-slate-900 py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-violet-400">
            How it works
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Three steps to your live startup
          </h2>
          <p className="mx-auto max-w-xl text-slate-400">
            AutoFounder AI compresses 4–7 months of startup work into a single, guided
            workflow — at a fraction of the cost.
          </p>
        </div>

        {/* Steps */}
        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step, idx) => {
            const Icon = step.icon
            return (
              <div key={step.number} className="relative">
                {/* Connector arrow between cards (desktop only) */}
                {idx < steps.length - 1 && (
                  <ArrowRight className="absolute -right-4 top-12 z-10 hidden h-8 w-8 text-slate-700 md:block" />
                )}

                <div className="h-full rounded-2xl border border-slate-800 bg-slate-950 p-8">
                  {/* Step number + icon row */}
                  <div className="mb-6 flex items-center gap-4">
                    <span className="text-5xl font-black text-slate-800/80">{step.number}</span>
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600/15 ring-1 ring-violet-500/30">
                      <Icon className="h-5 w-5 text-violet-400" />
                    </div>
                  </div>
                  <h3 className="mb-3 text-xl font-bold text-white">{step.title}</h3>
                  <p className="leading-relaxed text-slate-400">{step.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
