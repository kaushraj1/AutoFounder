import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/layout/Providers'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: {
    default: 'AutoFounder AI — Founder Portal',
    template: '%s | AutoFounder AI',
  },
  description:
    'A true AI co-founder that turns your idea into a live, validated software business — autonomously.',
  keywords: ['AI startup', 'autonomous agent', 'SaaS builder', 'AutoFounder'],
  authors: [{ name: 'Euron AutoFounder AI', url: 'https://euron.one' }],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
