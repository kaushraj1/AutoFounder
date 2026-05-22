import { CheckCircle, Code2, Cpu, Globe, LineChart, Megaphone } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Feature {
  icon: LucideIcon
  color: string
  bg: string
  title: string
  description: string
}

const features: Feature[] = [
  {
    icon: CheckCircle,
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    title: '30-Minute Idea Validation',
    description:
      'Market sizing (TAM/SAM/SOM), competitor discovery, 3–5 customer personas, Lean Canvas, and a 0–100 viability score — all in under 30 minutes.',
  },
  {
    icon: Cpu,
    color: 'text-violet-400',
    bg: 'bg-violet-400/10',
    title: 'Auto Architecture',
    description:
      'Full system design: entity-relationship diagrams, OpenAPI spec, tech stack selection, microservice boundaries, and a monthly cost forecast. You approve before we build.',
  },
  {
    icon: Code2,
    color: 'text-blue-400',
    bg: 'bg-blue-400/10',
    title: 'Full-Stack Code Generation',
    description:
      'Frontend + Backend + Database generated in parallel. Includes auth, Stripe payments, CI/CD pipeline, and test coverage ≥ 80%. Zero lint errors, guaranteed.',
  },
  {
    icon: LineChart,
    color: 'text-cyan-400',
    bg: 'bg-cyan-400/10',
    title: 'Self-Healing Tests',
    description:
      'Automated security scanning (Trivy, Semgrep, OWASP ZAP) plus unit and integration tests. The AI patches failures automatically — up to 5 retries before escalating.',
  },
  {
    icon: Globe,
    color: 'text-indigo-400',
    bg: 'bg-indigo-400/10',
    title: 'Deploy in 10 Minutes',
    description:
      'Containerized, cloud-provisioned, and live with DNS + SSL in under 10 minutes. Blue/green deploys with automatic rollback on failure included.',
  },
  {
    icon: Megaphone,
    color: 'text-pink-400',
    bg: 'bg-pink-400/10',
    title: 'AI-Powered Launch Kit',
    description:
      'Brand identity, landing page, 10 SEO blog posts, email drip sequences, and a social launch thread. Nothing goes live without your explicit sign-off.',
  },
]

export function Features() {
  return (
    <section id="features" className="bg-slate-950 py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-violet-400">
            Features
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Everything to go from idea to launch
          </h2>
          <p className="mx-auto max-w-2xl text-slate-400">
            Seven specialized AI agents work in parallel across every stage. You stay in control
            at four human-approval checkpoints — no engineering experience required.
          </p>
        </div>

        {/* Feature grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="group rounded-2xl border border-slate-800 bg-slate-900 p-8 transition-all hover:border-violet-500/40 hover:shadow-lg hover:shadow-violet-500/5"
              >
                <div className={`mb-5 inline-flex rounded-xl p-3 ${feature.bg}`}>
                  <Icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <h3 className="mb-3 text-lg font-semibold text-white">{feature.title}</h3>
                <p className="leading-relaxed text-slate-400">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
