'use client'

import { LogOut, Settings, User as UserIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useAppStore } from '@/lib/store'
import { supabase } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface HeaderProps {
  title?: string
}

export function Header({ title }: HeaderProps) {
  const { user } = useAppStore()
  const router = useRouter()

  async function handleLogout() {
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background px-6">
      {title && <h1 className="text-base font-semibold text-foreground">{title}</h1>}
      <div className="ml-auto flex items-center gap-2">
        {/* User menu */}
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10">
                <UserIcon className="h-3.5 w-3.5 text-primary" />
              </div>
              <span className="hidden text-sm sm:block">
                {user?.name ?? user?.email ?? 'Founder'}
              </span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xs">
            <DialogHeader>
              <DialogTitle>Account</DialogTitle>
              <DialogDescription>
                {user?.email ?? 'founder@autofounder.ai'}
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col gap-2">
              <Link href="/settings">
                <Button variant="outline" className="w-full justify-start gap-2">
                  <Settings className="h-4 w-4" />
                  Settings
                </Button>
              </Link>
            </div>
            <DialogFooter>
              <Button
                variant="destructive"
                className="w-full gap-2"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </header>
  )
}
