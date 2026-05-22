import { Zap } from 'lucide-react'

const footerLinks = {
  Product: [
    { label: 'Features', href: '#features' },
    { label: 'How It Works', href: '#how-it-works' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'Roadmap', href: '#' }, // TODO: Link to public roadmap
    { label: 'Changelog', href: '#' }, // TODO: Link to changelog page
  ],
  Company: [
    { label: 'About', href: '#' }, // TODO: Link to about page
    { label: 'Blog', href: '#' }, // TODO: Link to blog
    { label: 'Careers', href: '#' }, // TODO: Link to careers
    { label: 'Contact', href: 'mailto:autofounderai.co@gmail.com' },
  ],
  Legal: [
    { label: 'Privacy Policy', href: '#' }, // TODO: Link to privacy policy
    { label: 'Terms of Service', href: '#' }, // TODO: Link to ToS
    { label: 'Cookie Policy', href: '#' }, // TODO: Link to cookie policy
    { label: 'Security', href: '#' }, // TODO: Link to security page
  ],
}

export default function Footer() {
  return (
    <footer className="border-t border-white/5 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-12">
          {/* Brand column */}
          <div className="lg:col-span-2">
            <a href="#" className="flex items-center gap-2 mb-4 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg">
                <Zap size={16} className="text-white" />
              </div>
              <span className="font-bold text-lg text-white tracking-tight">
                AutoFounder <span className="text-blue-400">AI</span>
              </span>
            </a>
            <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
              A true AI co-founder that gets things done.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">
                {category}
              </h4>
              <ul className="flex flex-col gap-3">
                {links.map(({ label, href }) => (
                  <li key={label}>
                    <a
                      href={href}
                      className="text-sm text-slate-400 hover:text-white transition-colors duration-200"
                    >
                      {label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom row */}
        <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} AutoFounder AI. All rights reserved. Bengaluru,
            Karnataka, India.
          </p>
          <p className="text-xs text-slate-600">
            {/* TODO: Update tagline if brand voice changes */}
            Built with AutoFounder AI · autofounderai.co@gmail.com
          </p>
        </div>
      </div>
    </footer>
  )
}
