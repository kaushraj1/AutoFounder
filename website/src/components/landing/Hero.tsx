import { ArrowRight, Sparkles, Clock, DollarSign } from 'lucide-react'

const stats = [
  { icon: Clock, value: '~7 days', label: 'Idea → Live MVP' },
  { icon: DollarSign, value: '$200–$700', label: 'Total COGS' },
  { icon: Sparkles, value: '99%', label: 'Faster than traditional' },
]

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* Background glow */}
      <div className="absolute inset-0 hero-gradient pointer-events-none" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-300 text-sm font-medium mb-8">
          <Sparkles size={14} />
          {/* TODO: Update badge text closer to launch */}
          Now in Early Access — Limited Spots
        </div>

        {/* Headline */}
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]">
          Your Idea.{' '}
          <span className="gradient-text">Fully Built.</span>
          <br />
          In 7 Days.
        </h1>

        {/* Sub-headline */}
        <p className="max-w-2xl mx-auto text-lg sm:text-xl text-slate-400 mb-10 leading-relaxed">
          AutoFounder AI is a true AI co-founder that gets things done — autonomously validating,
          designing, building, testing, deploying, and marketing your software startup from a single
          text idea.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          {/* TODO: Wire up to actual waitlist form / auth flow */}
          <a
            href="#waitlist"
            className="group flex items-center gap-2 px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-base transition-all duration-200 shadow-lg shadow-blue-900/50 hover:shadow-blue-800/60 hover:scale-[1.02]"
          >
            Join the Waitlist
            <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </a>
          <a
            href="#video"
            className="flex items-center gap-2 px-8 py-4 rounded-xl border border-white/10 hover:border-white/20 text-slate-300 hover:text-white font-medium text-base transition-all duration-200 bg-white/5 hover:bg-white/10"
          >
            Watch Demo
          </a>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
          {stats.map(({ icon: Icon, value, label }) => (
            <div
              key={label}
              className="glass-card px-6 py-4 flex flex-col items-center gap-1"
            >
              <Icon size={18} className="text-blue-400 mb-1" />
              <span className="text-2xl font-bold text-white">{value}</span>
              <span className="text-xs text-slate-500">{label}</span>
            </div>
          ))}
        </div>

        {/* Scroll indicator */}
        <div className="mt-16 flex justify-center">
          <div className="w-px h-12 bg-gradient-to-b from-blue-500/50 to-transparent animate-pulse" />
        </div>
      </div>
    </section>
  )
}
