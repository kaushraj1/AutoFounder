import { Clock, DollarSign, TrendingDown } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface PainPoint {
  icon: LucideIcon
  iconColor: string
  iconBg: string
  cost: string
  title: string
  description: string
}

const painPoints: PainPoint[] = [
  {
    icon: Clock,
    iconColor: 'text-red-400',
    iconBg: 'bg-red-400/10',
    cost: '3 weeks + $5,000',
    title: 'Building the wrong thing',
    description:
      '90% of startups build products nobody wants. Traditional validation takes weeks of customer interviews and costly research — before you write a single line of code.',
  },
  {
    icon: DollarSign,
    iconColor: 'text-orange-400',
    iconBg: 'bg-orange-400/10',
    cost: '3–6 months + $50,000',
    title: 'MVPs are too expensive',
    description:
      'A typical MVP costs $15,000–$50,000 in contractor fees and takes months to ship. By the time you launch, the market has moved on.',
  },
  {
    icon: TrendingDown,
    iconColor: 'text-yellow-400',
    iconBg: 'bg-yellow-400/10',
    cost: '80% of launches fail',
    title: 'Launches fizzle out',
    description:
      'After months of building, founders face crickets on launch day. Without a GTM strategy baked in from day one, most products are invisible to their target market.',
  },
]

export function Problem() {
  return (
    <section className="bg-slate-900 py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            The founder journey is{' '}
            <span className="text-red-400">brutally hard</span>
          </h2>
          <p className="mx-auto max-w-2xl text-slate-400">
            Most startups fail not because of bad ideas — but because of slow, expensive,
            and fragmented execution.
          </p>
        </div>

        {/* Pain point cards */}
        <div className="grid gap-6 md:grid-cols-3">
          {painPoints.map((point) => {
            const Icon = point.icon
            return (
              <div
                key={point.title}
                className="rounded-2xl border border-slate-800 bg-slate-950 p-8 transition-colors hover:border-slate-700"
              >
                <div className={`mb-5 inline-flex rounded-xl p-3 ${point.iconBg}`}>
                  <Icon className={`h-6 w-6 ${point.iconColor}`} />
                </div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-slate-500">
                  Traditional path
                </p>
                <p className="mb-4 text-xl font-bold text-white">{point.cost}</p>
                <h3 className="mb-2 text-lg font-semibold text-white">{point.title}</h3>
                <p className="leading-relaxed text-slate-400">{point.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
