import { Check, Zap } from 'lucide-react'

// Pricing tiers sourced from CLAUDE.md §44
// TODO: Confirm final pricing and feature limits with business team before launch
const tiers = [
  {
    name: 'AI Researcher',
    subtitle: 'Solopreneur',
    price: '₹10,000',
    period: '/month',
    description: 'Perfect for solo founders and researchers validating a single idea.',
    highlight: false,
    badge: null,
    features: [
      '1 active build (Sandbox only)',
      'Market validation & Lean Canvas',
      'Architecture design & ERD',
      'Full-stack code generation',
      'Automated testing (≥80% coverage)',
      'Founder approval gates',
      'Community support',
      // TODO: Confirm exact feature limits
    ],
    cta: 'Start for ₹10,000/mo',
    ctaStyle: 'border border-white/15 hover:border-blue-500/50 text-white hover:bg-blue-500/10',
  },
  {
    name: 'Startup Founder',
    subtitle: 'Product Manager',
    price: '₹50,000',
    period: '/month',
    description: 'For serious founders who need multiple builds and live AWS deployments.',
    highlight: true,
    badge: 'Most Popular',
    features: [
      '5 active builds / month',
      'Everything in AI Researcher',
      '1-click AWS ECS Fargate deploy',
      'Custom domain + SSL automation',
      'Full GTM launch package',
      'Email drip sequences',
      'Priority support + Slack channel',
      // TODO: Confirm exact feature limits
    ],
    cta: 'Start for ₹50,000/mo',
    ctaStyle: 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/50',
  },
  {
    name: 'Enterprise',
    subtitle: 'Agency',
    price: 'Custom',
    period: '',
    description: 'For agencies and enterprises shipping at scale with dedicated infrastructure.',
    highlight: false,
    badge: null,
    features: [
      'Unlimited builds',
      'Everything in Startup Founder',
      'Dedicated VPC + private infra',
      'On-premises LLM option',
      'White-labeling & custom domain',
      'GDPR / SOC 2 / ISO 27001 ready',
      'Dedicated success manager + SLA',
      // TODO: Confirm enterprise SLA tiers
    ],
    cta: 'Contact Sales',
    ctaStyle: 'border border-white/15 hover:border-blue-500/50 text-white hover:bg-blue-500/10',
  },
]

export default function Pricing() {
  return (
    <section id="pricing" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Simple, transparent pricing
          </h2>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            All plans include a human-approval gate at every critical milestone — you're always in
            control.
          </p>
          {/* TODO: Add annual discount toggle when billing is wired up */}
        </div>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {tiers.map(
            ({ name, subtitle, price, period, description, highlight, badge, features, cta, ctaStyle }) => (
              <div
                key={name}
                className={`relative rounded-2xl p-8 flex flex-col gap-6 ${
                  highlight
                    ? 'bg-gradient-to-b from-blue-600/20 to-blue-600/5 border border-blue-500/40 glow-blue'
                    : 'glass-card'
                }`}
              >
                {/* Popular badge */}
                {badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="flex items-center gap-1.5 px-4 py-1 rounded-full bg-blue-600 text-white text-xs font-bold shadow-lg">
                      <Zap size={11} />
                      {badge}
                    </span>
                  </div>
                )}

                {/* Tier header */}
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-1">
                    {subtitle}
                  </p>
                  <h3 className="text-xl font-bold text-white mb-3">{name}</h3>
                  <div className="flex items-end gap-1 mb-3">
                    <span className="text-4xl font-extrabold text-white">{price}</span>
                    {period && <span className="text-slate-400 text-sm mb-1">{period}</span>}
                  </div>
                  <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
                </div>

                {/* Features */}
                <ul className="flex flex-col gap-3 flex-1">
                  {features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3">
                      <Check
                        size={16}
                        className={`mt-0.5 flex-shrink-0 ${highlight ? 'text-blue-400' : 'text-emerald-400'}`}
                      />
                      <span className="text-slate-300 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                {/* TODO: Wire up to billing / Stripe checkout */}
                <a
                  href="#waitlist"
                  className={`block text-center px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${ctaStyle}`}
                >
                  {cta}
                </a>
              </div>
            )
          )}
        </div>

        {/* Footnote */}
        <p className="text-center text-slate-500 text-sm mt-10">
          All plans include a 7-day free trial. No credit card required to join the waitlist.{' '}
          {/* TODO: Confirm trial terms with business team */}
        </p>
      </div>
    </section>
  )
}
