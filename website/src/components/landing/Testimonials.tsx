import { Star, Quote } from 'lucide-react'

// TODO: Replace all testimonials below with real user quotes before launch.
// Mark source with name, role, company, and optionally a photo URL.
const testimonials = [
  {
    name: 'Priya S.',
    role: 'Solo Founder',
    company: 'Bengaluru, IN',
    initials: 'PS',
    quote:
      "I had an idea for a B2B SaaS tool on Monday. By Wednesday, AutoFounder AI had validated the market, built the MVP, and deployed it to AWS. I spent the week reviewing, not building.",
    stars: 5,
  },
  {
    name: 'Marcus T.',
    role: 'Product Manager turned Founder',
    company: 'London, UK',
    initials: 'MT',
    quote:
      "The self-healing loop blew my mind. It wrote 87 tests, 3 failed, and fixed them all without me touching a line of code. Final coverage was 84%. I have never shipped with that confidence before.",
    stars: 5,
  },
  {
    name: 'Ananya K.',
    role: 'Early-Stage Investor',
    company: 'Portfolio advisor',
    initials: 'AK',
    quote:
      "I am recommending AutoFounder AI to every pre-seed founder in my portfolio. The Lean Canvas + market sizing output alone is worth the subscription. It is what you would pay a consultant $5K for.",
    stars: 5,
  },
  {
    name: 'David L.',
    role: 'Agency Owner',
    company: 'San Francisco, US',
    initials: 'DL',
    quote:
      "We use the Enterprise tier to ship MVPs for clients. Time to first demo dropped from 6 weeks to 5 days. Our margins went up 40% and our clients think we are wizards.",
    stars: 5,
  },
  {
    name: 'Rahul M.',
    role: 'Technical Founder',
    company: 'Pune, IN',
    initials: 'RM',
    quote:
      "The architecture agent's ERD and OpenAPI spec were better than what I would have designed manually in 2 days. It even caught a scaling bottleneck I would have missed until production.",
    stars: 5,
  },
  {
    name: 'Sophie B.',
    role: 'Non-technical Founder',
    company: 'Paris, FR',
    initials: 'SB',
    quote:
      "I have zero coding background. AutoFounder AI handled everything. I just reviewed each milestone and clicked Approve. My SaaS has 200 paying users and I still have not written a single line of code.",
    stars: 5,
  },
]

export default function Testimonials() {
  return (
    <section id="testimonials" className="py-24 section-gradient">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-blue-400 text-sm font-semibold uppercase tracking-widest mb-3">
            Social Proof
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Founders love AutoFounder AI
          </h2>
          <p className="text-slate-400 text-lg">
            {/* TODO: Replace with real user count / launch metric */}
            <span className="text-white font-semibold">500+ founders</span> on the waitlist.{' '}
            Early access cohort launching soon.
          </p>
          <p className="text-xs text-slate-600 mt-2 italic">
            Placeholder testimonials — all quotes are illustrative and will be replaced with real user reviews before public launch.
          </p>
        </div>

        {/* Testimonial grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map(({ name, role, company, initials, quote, stars }) => (
            <div
              key={name}
              className="glass-card p-6 flex flex-col gap-4 hover:border-white/15 transition-colors duration-200"
            >
              {/* Stars */}
              <div className="flex gap-1">
                {Array.from({ length: stars }).map((_, i) => (
                  <Star key={i} size={14} className="text-amber-400 fill-amber-400" />
                ))}
              </div>

              {/* Quote */}
              <div className="relative flex-1">
                <Quote size={20} className="text-blue-500/40 absolute -top-1 -left-1" />
                <p className="text-slate-300 text-sm leading-relaxed pl-4">{quote}</p>
              </div>

              {/* Author */}
              <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                {/* TODO: Replace initials avatar with real photo once available */}
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-600 to-blue-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                  {initials}
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{name}</p>
                  <p className="text-xs text-slate-500">
                    {role} &middot; {company}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
