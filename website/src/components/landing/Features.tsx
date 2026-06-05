import { Brain, Layers, Code2, Rocket, Megaphone, ShieldCheck, BarChart3 } from "lucide-react";

const features = [
  {
    icon: Brain,
    color: "blue",
    title: "Autonomous Market Validation",
    description:
      "The Strategy Agent scans competitors, sizes your market (TAM/SAM/SOM), generates ICPs, and produces a full Lean Canvas with viability score — in under 30 minutes.",
    badge: "Pillar 1",
  },
  {
    icon: Layers,
    color: "violet",
    title: "Architecture & Tech Stack Design",
    description:
      "The Architect Agent extracts requirements, designs your DB schema (ERD), generates an OpenAPI contract, selects the optimal tech stack, and produces a cost forecast — then waits for your approval before a line of code is written.",
    badge: "Pillar 2",
  },
  {
    icon: Code2,
    color: "sky",
    title: "Full-Stack Code Generation",
    description:
      "The Engineering Agent scaffolds your entire repo: Next.js 14 frontend, FastAPI backend, PostgreSQL schema, auth (OAuth/JWT), Stripe integration, and Dockerfile — all TypeScript-strict and linting-clean.",
    badge: "Pillar 3",
  },
  {
    icon: ShieldCheck,
    color: "emerald",
    title: "Autonomous Testing & Self-Healing",
    description:
      "Generates unit, integration, and security tests. If tests fail, a self-healing loop attempts up to 5 auto-fix cycles — targeting ≥80% coverage and ≥90% auto-fix rate.",
    badge: "Pillar 4",
  },
  {
    icon: Rocket,
    color: "cyan",
    title: "One-Click AWS Deployment",
    description:
      "Containerizes your app, writes Terraform IaC, provisions ECS Fargate + RDS + Redis, configures SSL via ACM, and sets up CI/CD — from code to live in under 10 minutes.",
    badge: "Pillar 5",
  },
  {
    icon: Megaphone,
    color: "pink",
    title: "Full GTM Launch Package",
    description:
      "Generates your brand identity, landing page, SEO blog posts, Product Hunt kit, email drip sequences, and launch threads for X/LinkedIn/Reddit — founder approves before anything goes live.",
    badge: "Pillar 6",
  },
  {
    icon: BarChart3,
    color: "amber",
    title: "Continuous LLMOps & Growth",
    description:
      "After launch, the LLMOps Agent tracks user feedback, optimizes prompts with DSPy, detects model drift, runs A/B experiments, and delivers weekly improvement cycles.",
    badge: "Pillar 7",
  },
];

const colorMap: Record<string, string> = {
  blue: "bg-blue-500/10 border-blue-500/20 text-blue-400",
  violet: "bg-violet-500/10 border-violet-500/20 text-violet-400",
  sky: "bg-sky-500/10 border-sky-500/20 text-sky-400",
  emerald: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
  cyan: "bg-cyan-500/10 border-cyan-500/20 text-cyan-400",
  pink: "bg-pink-500/10 border-pink-500/20 text-pink-400",
  amber: "bg-amber-500/10 border-amber-500/20 text-amber-400",
};

const badgeMap: Record<string, string> = {
  blue: "bg-blue-500/10 text-blue-400",
  violet: "bg-violet-500/10 text-violet-400",
  sky: "bg-sky-500/10 text-sky-400",
  emerald: "bg-emerald-500/10 text-emerald-400",
  cyan: "bg-cyan-500/10 text-cyan-400",
  pink: "bg-pink-500/10 text-pink-400",
  amber: "bg-amber-500/10 text-amber-400",
};

export default function Features() {
  return (
    <section id="features" className="py-24 section-gradient">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Everything a founding team does — <span className="gradient-text">done by AI.</span>
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Seven specialized AI agents cover every pillar of startup creation, collaborating
            through a LangGraph orchestration engine with human-approval gates at every critical
            step.
          </p>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:[&>*:last-child]:col-start-2">
          {features.map(({ icon: Icon, color, title, description, badge }) => (
            <div
              key={title}
              className="glass-card p-6 flex flex-col gap-4 hover:border-white/15 transition-colors duration-200 group"
            >
              <div className="flex items-start justify-between">
                <div
                  className={`w-11 h-11 rounded-xl border flex items-center justify-center flex-shrink-0 ${colorMap[color]}`}
                >
                  <Icon size={20} />
                </div>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full ${badgeMap[color]}`}
                >
                  {badge}
                </span>
              </div>
              <h3 className="text-base font-semibold text-white leading-snug">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed flex-1">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
