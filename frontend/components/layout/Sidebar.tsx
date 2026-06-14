'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Rocket,
  Plus,
  Settings,
  CreditCard,
  Zap,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/lib/store'
import { Button } from '@/components/ui/button'

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/ideas/new', label: 'New Idea', icon: Plus },
  { href: '/runs', label: 'All Runs', icon: Rocket },
  { href: '/settings', label: 'Settings', icon: Settings },
  { href: '/billing', label: 'Billing', icon: CreditCard },
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, setSidebarOpen } = useAppStore()

  return (
    <aside
      className={cn(
        'flex h-screen flex-col border-r bg-card transition-all duration-200',
        sidebarOpen ? 'w-56' : 'w-14'
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center border-b px-3">
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md bg-primary">
            <Zap className="h-4 w-4 text-primary-foreground" />
          </div>
          {sidebarOpen && (
            <span className="text-sm font-bold tracking-tight text-foreground">
              AutoFounder<span className="text-primary"> AI</span>
            </span>
          )}
        </div>
      </div>

      {/* Nav */}
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-2">
        {NAV_ITEMS.map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== '/dashboard' && pathname.startsWith(item.href))
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t p-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-full"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      </div>
    </aside>
  )
}
