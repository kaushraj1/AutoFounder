import { useState } from "react";
import { ChevronDown } from "lucide-react";

// TODO: Review and update FAQ answers with product/legal team before launch
const faqs = [
  {
    q: "Who owns the code and IP that AutoFounder AI generates?",
    a: "You do — 100%. All generated code, architecture docs, marketing assets, and deployment artifacts are owned by you and your company. AutoFounder AI is a tool, not a co-founder with equity.",
  },
  {
    q: "Do I need technical knowledge to use AutoFounder AI?",
    a: "No. AutoFounder AI is designed for both technical and non-technical founders. You describe your idea in plain English, review milestone outputs (Lean Canvas, architecture diagrams, code previews), and click Approve or Request Changes. The agents handle all the technical work.",
  },
  {
    q: "How does the human-approval gate work?",
    a: "At every critical milestone — market validation, architecture design, infrastructure spend, and public launch — the system pauses and waits for your explicit approval. Nothing is deployed or published without your sign-off. You can request changes, pivot the direction, or approve and continue at each gate.",
  },
  {
    q: "What happens if the generated code has bugs?",
    a: "The Testing & Self-Healing agent (Pillar 4) runs automated tests and attempts up to 5 self-correction cycles before escalating to you. The target is ≥90% auto-fix rate and ≥80% test coverage. If issues can't be resolved automatically, you're notified with a detailed report so you or your team can step in.",
  },
  {
    q: "Which cloud provider does AutoFounder AI deploy to?",
    a: "By default, deployments target Amazon ECS on Fargate (multi-AZ) with RDS PostgreSQL, ElastiCache Redis, S3, and ACM-managed SSL. Enterprise plans include support for custom AWS accounts, dedicated VPCs, and — coming soon — multi-cloud options (GCP, Azure). The generated Terraform IaC is yours to inspect and modify.",
  },
  {
    q: "Is my idea and data kept private?",
    a: "Yes. All data is tenant-isolated at every layer: separate database schemas, namespace-per-tenant in the vector store, and S3 paths prefixed by your tenant ID. Data is encrypted at rest (AES-256 + KMS) and in transit (TLS 1.3). We are GDPR-compliant, including right-to-erasure on request.",
  },
];

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-white/8 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-4 py-5 text-left group"
        aria-expanded={open}
      >
        <span className="text-base font-medium text-white group-hover:text-blue-300 transition-colors">
          {q}
        </span>
        <ChevronDown
          size={18}
          className={`flex-shrink-0 text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && <p className="pb-5 text-slate-400 text-sm leading-relaxed">{a}</p>}
    </div>
  );
}

export default function FAQ() {
  return (
    <section id="faq" className="py-24 section-gradient">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Frequently asked questions
          </h2>
          <p className="text-slate-400">
            Have a question that isn't here?{" "}
            {/* TODO: Replace with real support email / chat link */}
            <a
              href="mailto:autofounderai.co@gmail.com"
              className="text-blue-400 hover:text-blue-300 underline underline-offset-4 transition-colors"
            >
              Email us
            </a>
            .
          </p>
        </div>

        {/* Accordion */}
        <div className="glass-card px-6">
          {faqs.map((faq) => (
            <FAQItem key={faq.q} q={faq.q} a={faq.a} />
          ))}
        </div>
      </div>
    </section>
  );
}
