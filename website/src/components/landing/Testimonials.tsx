import { Star } from 'lucide-react'

// TODO: Replace ALL placeholder testimonials with verified customer quotes before launch.
// Collect feedback via product@euron.one or the in-app feedback flow.
const testimonials = [
  {
    initials: 'JD',
    // TODO: Replace with real customer name
    name: '[Founder Name]',
    // TODO: Replace with real role and company
    role: '[Founder @ Company]',
    // TODO: Replace with verified quote
    quote:
      'AutoFounder AI saved us 4 months of development time. We went from idea to paying customers in 11 days.',
  },
  {
    initials: 'SM',
    name: '[Founder Name]',
    role: '[CEO, Startup Name]',
    quote:
      "I'm a non-technical founder. Before AutoFounder AI, I'd spent ₹25 lakhs on contractors for a half-finished product. Now I ship weekly.",
  },
  {
    initials: 'AK',
    name: '[Product Leader Name]',
    role: '[Product Manager, Company]',
    quote:
      'The validation alone is worth the subscription. We pivoted twice in the first hour based on the competitor analysis — our third idea scored 87/100.',
  },
]

export function Testimonials() {
  return (
    <section className="bg-slate-950 py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Placeholder badge */}
        <div className="mb-8 flex justify-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-400">
            {/* TODO: Remove this badge once real testimonials are added */}
            ⚠️ Placeholder testimonials — not real customers yet
          </div>
        </div>

        {/* Header */}
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Loved by founders
          </h2>
          {/* TODO: Replace with real count once available (e.g. "Join 2,400+ founders") */}
          <p className="text-slate-400">
            Join the waitlist and be among the first to ship faster with AutoFounder AI
          </p>
        </div>

        {/* Testimonial cards */}
        <div className="grid gap-6 md:grid-cols-3">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="flex flex-col rounded-2xl border border-slate-800 bg-slate-900 p-8"
            >
              {/* Stars */}
              <div className="mb-4 flex gap-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
                ))}
              </div>

              {/* Quote */}
              <p className="mb-6 flex-1 leading-relaxed text-slate-300">"{t.quote}"</p>

              {/* Author */}
              <div className="flex items-center gap-3">
                {/* TODO: Replace initials avatar with real photo (use <img> with src) */}
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-violet-600 text-sm font-bold text-white">
                  {t.initials}
                </div>
                <div>
                  <p className="font-semibold text-white">{t.name}</p>
                  <p className="text-sm text-slate-500">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
