import { Check } from 'lucide-react'

// TODO: Confirm final pricing with the finance team before launch.
// Source: CLAUDE.md §44 / MEMORY.md product identity
const plans = [
  {
    name: 'Solopreneur',
    // TODO: Add USD equivalent once international pricing is confirmed
    price: '₹10,000',
    period: '/month',
    description: 'Perfect for solo founders validating their first idea.',
    badge: null,
    features: [
      '1 active build at a time',
      'Sandbox deployment (no custom domain)',
      'Strategy + Architecture + Code agents',
      '30-day build history',
      'Community support',
    ],
    cta: 'Start Free Trial',
    // TODO: Link to Stripe checkout once payment is wired up
    ctaHref: '#waitlist',
    popular: false,
  },
  {
    name: 'Startup',
    price: '₹50,000',
    period: '/month',
    description: 'For teams moving fast and shipping real products.',
    badge: 'Most Popular',
    features: [
      '5 builds per month',
      '1-click cloud deploy (custom domain + SSL)',
      'All 7 AI agents',
      'Priority build queue',
      'GitHub repo + CI/CD pipeline',
      'Unlimited build history',
      'Priority email support',
    ],
    cta: 'Get Early Access',
    ctaHref: '#waitlist',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For agencies and studios shipping at scale.',
    badge: null,
    features: [
      'Unlimited builds',
      'Dedicated cloud infrastructure',
      'On-premises LLM option',
      'White-labeling',
      'GDPR + SOC 2 compliance pack',
      'Custom SLA',
      'Dedicated account manager',
    ],
    cta: 'Contact Sales',
    ctaHref: 'mailto:product@euron.one',
    popular: false,
  },
]

export function Pricing() {
  return (
    <section id="pricing" className="bg-slate-900 py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-violet-400">
            Pricing
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Simple, transparent pricing
          </h2>
          {/* TODO: Confirm whether there's a free trial before launch */}
          <p className="mx-auto max-w-xl text-slate-400">
            Start free. Upgrade when you're ready to ship your first product.
          </p>
        </div>

        {/* Plan cards */}
        <div className="grid gap-8 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-2xl p-8 ${
                plan.popular
                  ? 'border-2 border-violet-500 bg-slate-950 shadow-2xl shadow-violet-500/10'
                  : 'border border-slate-800 bg-slate-950'
              }`}
            >
              {/* Popular badge */}
              {plan.badge && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="rounded-full bg-violet-600 px-3 py-1 text-xs font-semibold text-white">
                    {plan.badge}
                  </span>
                </div>
              )}

              {/* Plan header */}
              <div className="mb-6">
                <h3 className="mb-1 text-lg font-bold text-white">{plan.name}</h3>
                <p className="mb-5 text-sm text-slate-400">{plan.description}</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-black text-white">{plan.price}</span>
                  {plan.period && <span className="text-slate-400">{plan.period}</span>}
                </div>
              </div>

              {/* CTA */}
              <a
                href={plan.ctaHref}
                className={`mb-8 block rounded-xl px-6 py-3.5 text-center text-sm font-semibold transition-all ${
                  plan.popular
                    ? 'bg-violet-600 text-white hover:bg-violet-500 hover:shadow-lg hover:shadow-violet-500/25'
                    : 'border border-slate-700 bg-slate-900 text-white hover:border-slate-600'
                }`}
              >
                {plan.cta}
              </a>

              {/* Feature list */}
              <ul className="mt-auto space-y-3.5">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <Check className="mt-0.5 h-4 w-4 flex-shrink-0 text-violet-400" />
                    <span className="text-sm text-slate-400">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
