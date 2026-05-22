import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

const faqs = [
  {
    question: 'What exactly does AutoFounder AI build?',
    answer:
      'AutoFounder AI produces a complete software startup: a validated business model (Lean Canvas, viability score, competitor analysis), a full-stack codebase (frontend + backend + database), a configured cloud deployment with DNS and SSL, and a marketing launch kit including a landing page, SEO blog posts, email sequences, and social posts. Everything is generated autonomously and reviewed by you at four key checkpoints.',
  },
  {
    question: 'How long does a full build actually take?',
    answer:
      'Idea validation completes in under 30 minutes. A complete, deployed MVP takes approximately 7 days. The marketing and launch kit is ready within 2 hours of deployment approval. Build times may vary by product complexity — enterprise-grade products with many integrations can take longer.',
  },
  {
    question: 'Do I need to be technical to use it?',
    answer:
      'No. AutoFounder AI handles all engineering decisions autonomously. You review and approve at four human-in-the-loop checkpoints: idea validation, system architecture, infrastructure spend approval, and public launch. No coding, DevOps knowledge, or design skills are required.',
  },
  {
    question: 'Is my idea secure and private?',
    answer:
      'Yes. Every build runs in a fully isolated tenant environment with schema-per-organization database isolation and row-level security. Your idea, source code, and business data are never shared across accounts. All infrastructure runs on encrypted storage and encrypted connections.',
  },
  {
    question: 'What happens after my MVP launches?',
    answer:
      'The LLMOps agent continuously monitors your product performance, optimises AI prompts based on real user feedback, tracks token and compute costs per build, and surfaces weekly improvement reports. Your product keeps getting smarter without any manual work from you.',
  },
]

export function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  return (
    <section id="faq" className="bg-slate-950 py-24">
      <div className="mx-auto max-w-3xl px-6">
        {/* Header */}
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-violet-400">
            FAQ
          </p>
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Common questions
          </h2>
          <p className="text-slate-400">
            Still have questions?{' '}
            <a
              href="mailto:product@euron.one"
              className="text-violet-400 underline underline-offset-2 hover:text-violet-300"
            >
              Reach out to us
            </a>
            .
          </p>
        </div>

        {/* Accordion */}
        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openIdx === idx
            return (
              <div
                key={faq.question}
                className={`rounded-2xl border transition-colors duration-200 ${
                  isOpen
                    ? 'border-violet-500/40 bg-slate-900'
                    : 'border-slate-800 bg-slate-900 hover:border-slate-700'
                }`}
              >
                <button
                  className="flex w-full items-center justify-between gap-4 p-6 text-left"
                  onClick={() => setOpenIdx(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                >
                  <span className="font-semibold text-white">{faq.question}</span>
                  <ChevronDown
                    className={`h-5 w-5 flex-shrink-0 text-slate-400 transition-transform duration-200 ${
                      isOpen ? 'rotate-180 text-violet-400' : ''
                    }`}
                  />
                </button>

                {isOpen && (
                  <div className="px-6 pb-6">
                    <p className="leading-relaxed text-slate-400">{faq.answer}</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
