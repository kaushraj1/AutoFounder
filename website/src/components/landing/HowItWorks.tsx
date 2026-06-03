import { Lightbulb, Cpu, Globe } from "lucide-react";

const steps = [
  {
    step: "01",
    icon: Lightbulb,
    title: "Describe Your Idea",
    description:
      "Type your startup idea in plain English — or upload a PDF, voice note, or URL. AutoFounder AI ingests it, clarifies ambiguities, and kicks off the autonomous pipeline.",
    detail:
      "Strategy Agent validates your market in < 30 min with full Lean Canvas + viability score.",
  },
  {
    step: "02",
    icon: Cpu,
    title: "Agents Build Everything",
    description:
      "Seven specialized AI agents handle architecture, code generation, testing, and self-healing in parallel — with human-approval gates at every critical milestone so you stay in control.",
    detail:
      "Frontend + Backend + DB + Auth + Stripe + CI/CD — all production-grade, zero linting errors.",
  },
  {
    step: "03",
    icon: Globe,
    title: "Launch to the World",
    description:
      "Your product is deployed to AWS ECS Fargate with a live URL, custom domain, SSL certificate, and a full GTM package: landing page, SEO content, social posts, and email drip sequences.",
    detail:
      "Code → Live in < 10 min. Marketing assets delivered in < 2 hours. You approve before anything goes public.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">How it works</h2>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Three steps stand between your idea and a live, marketed software business.
          </p>
        </div>

        {/* Steps */}
        <div className="relative">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
            {steps.map(({ step, icon: Icon, title, description, detail }, i) => (
              <div key={step} className="flex flex-col items-center text-center gap-5 relative">
                {/* Step circle */}
                <div className="relative flex-shrink-0">
                  <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-blue-600/20 to-blue-600/20 border border-blue-500/30 flex flex-col items-center justify-center gap-1 shadow-lg">
                    <Icon size={28} className="text-blue-400" />
                    <span className="text-[10px] font-bold text-blue-500 tracking-widest">
                      {step}
                    </span>
                  </div>
                  {/* Connector arrow for mobile */}
                  {i < steps.length - 1 && (
                    <div className="lg:hidden flex justify-center mt-6">
                      <div className="w-px h-8 bg-gradient-to-b from-blue-500/50 to-transparent" />
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed mb-4">{description}</p>
                  <div className="inline-block px-4 py-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 leading-snug">
                    {detail}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          {/* TODO: Link to actual waitlist / sign-up page */}
          <a
            href="#waitlist"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-base transition-all duration-200 shadow-lg shadow-blue-900/50 hover:scale-[1.02]"
          >
            Start Building Your Startup →
          </a>
        </div>
      </div>
    </section>
  );
}
