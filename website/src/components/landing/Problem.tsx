import { AlertCircle, Clock, Banknote, TrendingDown } from "lucide-react";

const problems = [
  {
    icon: TrendingDown,
    title: "90% of startups build things nobody wants",
    description:
      "Founders spend 3+ weeks and $5,000+ on market validation — only to discover there's no real demand. Most skip it entirely and ship straight into a dead market.",
  },
  {
    icon: Clock,
    title: "MVPs take 3–6 months and cost $15K–$50K",
    description:
      "Hiring a dev agency, debating the tech stack, onboarding contractors, reviewing code, managing scope creep — by the time your MVP ships, the window has closed.",
  },
  {
    icon: Banknote,
    title: "Launch fizzles with zero traction",
    description:
      "Even great products fail at launch. Setting up SEO, writing copy, building a social presence, and coordinating Product Hunt takes another 2–3 weeks after the build is done.",
  },
];

const comparison = [
  { stage: "Idea → Validated", traditional: "3 weeks", autofounder: "30 minutes" },
  { stage: "Validated → MVP built", traditional: "3–6 months", autofounder: "7 days" },
  { stage: "MVP → Deployed", traditional: "1 week", autofounder: "10 minutes" },
  { stage: "Deployed → Marketed", traditional: "2–3 weeks", autofounder: "2 hours" },
];

export default function Problem() {
  return (
    <section id="problem" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium mb-6">
            <AlertCircle size={14} />
            The Problem
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Building a startup is broken.
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            The traditional path from idea to live product costs $20K–$60K and takes 4–7 months.
            Most founders never even reach launch.
          </p>
        </div>

        {/* Pain points */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
          {problems.map(({ icon: Icon, title, description }) => (
            <div key={title} className="glass-card p-6 flex flex-col gap-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0">
                <Icon size={20} className="text-red-400" />
              </div>
              <h3 className="text-base font-semibold text-white leading-snug">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
            </div>
          ))}
        </div>

        {/* Comparison table */}
        <div className="max-w-3xl mx-auto">
          <h3 className="text-center text-xl font-semibold text-white mb-8">
            Traditional path vs. AutoFounder AI
          </h3>
          <div className="glass-card overflow-hidden">
            <div className="grid grid-cols-3 bg-white/5 px-6 py-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              <span>Stage</span>
              <span className="text-center text-red-400">Traditional</span>
              <span className="text-center text-blue-400">AutoFounder AI</span>
            </div>
            {comparison.map(({ stage, traditional, autofounder }, i) => (
              <div
                key={stage}
                className={`grid grid-cols-3 px-6 py-4 items-center ${
                  i < comparison.length - 1 ? "border-b border-white/5" : ""
                }`}
              >
                <span className="text-sm text-slate-300">{stage}</span>
                <span className="text-center text-sm text-red-400 font-medium line-through opacity-70">
                  {traditional}
                </span>
                <span className="text-center text-sm text-blue-300 font-bold">{autofounder}</span>
              </div>
            ))}
            <div className="grid grid-cols-3 px-6 py-4 bg-blue-500/5 border-t border-blue-500/20">
              <span className="text-sm font-bold text-white">Total</span>
              <span className="text-center text-sm text-red-400 font-bold line-through opacity-70">
                4–7 months · $20K–$60K
              </span>
              <span className="text-center text-sm text-blue-300 font-bold">
                ~7 days · $200–$700
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
