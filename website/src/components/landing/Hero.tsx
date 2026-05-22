import { ArrowRight, Sparkles } from 'lucide-react'

const stats = [
  { value: '30 min', label: 'Idea validated' },
  { value: '7 days', label: 'MVP built' },
  { value: '10 min', label: 'Deployed live' },
  { value: '$200–$700', label: 'Total cost' },
]

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-slate-950 pb-24 pt-32">
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[700px] w-[700px] -translate-x-1/2 rounded-full bg-violet-600/15 blur-3xl" />
        <div className="absolute right-0 top-1/2 h-96 w-96 rounded-full bg-cyan-500/8 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-64 w-64 rounded-full bg-violet-800/10 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-5xl px-6 text-center">
        {/* Badge */}
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-sm text-violet-300">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Phase 1 Now Live — Join the Waitlist</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </div>

        {/* Headline */}
        <h1 className="mb-6 text-5xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-6xl lg:text-7xl">
          Turn any idea into a{' '}
          <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
            live startup
          </span>
          {' '}— in 7 days
        </h1>

        {/* Sub-headline */}
        <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-slate-400 sm:text-xl">
          AutoFounder AI validates your idea, architects the system, writes the code, deploys
          the infrastructure, and launches the marketing — autonomously. You stay in control
          at every step.
        </p>

        {/* CTAs */}
        <div className="mb-16 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a
            href="#waitlist"
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-violet-500/25 transition-all hover:bg-violet-500 hover:shadow-violet-500/40 sm:w-auto"
          >
            Get Early Access
            <ArrowRight className="h-4 w-4" />
          </a>
          <a
            href="#video"
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-900/80 px-8 py-4 text-base font-semibold text-slate-300 transition-all hover:border-slate-600 hover:text-white sm:w-auto"
          >
            Watch Demo
          </a>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.value}
              className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 backdrop-blur-sm"
            >
              <div className="text-2xl font-bold text-white sm:text-3xl">{stat.value}</div>
              <div className="mt-1 text-sm text-slate-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
