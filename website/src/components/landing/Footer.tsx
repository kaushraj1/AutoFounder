import { Zap } from 'lucide-react'
import { useState } from 'react'

// TODO: Replace '#' hrefs with real page URLs once those pages exist
const footerLinks = [
  {
    heading: 'Product',
    links: [
      { label: 'Features', href: '#features' },
      { label: 'How it works', href: '#how-it-works' },
      { label: 'Pricing', href: '#pricing' },
      { label: 'Changelog', href: '#' }, // TODO: Add changelog page
    ],
  },
  {
    heading: 'Company',
    links: [
      { label: 'About', href: '#' }, // TODO: Add about page
      { label: 'Blog', href: '#' }, // TODO: Add blog
      { label: 'Careers', href: '#' }, // TODO: Add careers page
      { label: 'Contact', href: 'mailto:product@euron.one' },
    ],
  },
  {
    heading: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '#' }, // TODO: Add privacy policy
      { label: 'Terms of Service', href: '#' }, // TODO: Add terms of service
      { label: 'Cookie Policy', href: '#' }, // TODO: Add cookie policy
    ],
  },
]

// TODO: Replace '#' with real social media profile URLs
const socialLinks = [
  { name: 'X', label: '𝕏', href: '#' },
  { name: 'LinkedIn', label: 'in', href: '#' },
  { name: 'GitHub', label: 'GH', href: '#' },
]

export function Footer() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // TODO: Wire up to backend POST /v1/waitlist endpoint
    // For now, just show a success state
    setSubmitted(true)
    setEmail('')
  }

  return (
    <footer className="border-t border-slate-800 bg-slate-950">
      {/* Waitlist / CTA band */}
      <div id="waitlist" className="border-b border-slate-800 py-20">
        <div className="mx-auto max-w-2xl px-6 text-center">
          {/* Glow */}
          <div className="pointer-events-none absolute left-1/2 -translate-x-1/2 h-64 w-96 rounded-full bg-violet-600/10 blur-3xl" />

          <h2 className="relative mb-3 text-3xl font-bold text-white sm:text-4xl">
            Ready to build your startup?
          </h2>
          <p className="relative mb-8 text-slate-400">
            {/* TODO: Confirm early-access offer details with marketing team */}
            Join the waitlist. Early access members get 3 months free on the Startup plan.
          </p>

          {submitted ? (
            <div className="relative rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-6 py-4 text-emerald-400">
              ✓ You're on the list — we'll be in touch soon!
            </div>
          ) : (
            <form
              onSubmit={handleSubmit}
              className="relative flex flex-col gap-3 sm:flex-row"
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3.5 text-white placeholder:text-slate-500 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
              />
              <button
                type="submit"
                className="rounded-xl bg-violet-600 px-6 py-3.5 font-semibold text-white transition-all hover:bg-violet-500 hover:shadow-lg hover:shadow-violet-500/25"
              >
                Join Waitlist
              </button>
            </form>
          )}

          <p className="relative mt-3 text-xs text-slate-600">
            No spam. Unsubscribe anytime.
          </p>
        </div>
      </div>

      {/* Main footer body */}
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="grid gap-12 lg:grid-cols-4">
          {/* Brand column */}
          <div className="lg:col-span-1">
            <a href="#" className="mb-5 flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
                <Zap className="h-4 w-4 text-white" />
              </div>
              <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-lg font-bold text-transparent">
                AutoFounder AI
              </span>
            </a>
            <p className="mb-6 text-sm leading-relaxed text-slate-400">
              A true AI co-founder that gets things done.
            </p>

            {/* Social icons */}
            {/* TODO: Add real URLs before launch */}
            <div className="flex gap-2">
              {socialLinks.map((s) => (
                <a
                  key={s.name}
                  href={s.href}
                  aria-label={s.name}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 text-xs font-bold text-slate-400 transition-colors hover:border-slate-600 hover:text-white"
                >
                  {s.label}
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {footerLinks.map((col) => (
            <div key={col.heading}>
              <h4 className="mb-4 text-sm font-semibold text-white">{col.heading}</h4>
              <ul className="space-y-3">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-slate-400 transition-colors hover:text-white"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-slate-800 pt-8 sm:flex-row">
          <p className="text-sm text-slate-500">
            © 2026 Euron AutoFounder AI, Bengaluru, Karnataka, India. All rights reserved.
          </p>
          <p className="text-xs text-slate-600">
            {/* TODO: Add version number once versioning is established */}
            Built with 7 AI agents · product@euron.one
          </p>
        </div>
      </div>
    </footer>
  )
}
