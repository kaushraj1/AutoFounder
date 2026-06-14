'use client'

import { useState } from 'react'
import { Save, Copy, Eye, EyeOff, Trash2, AlertTriangle } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
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

export default function SettingsPage() {
  const { user } = useAppStore()
  const [name, setName] = useState(user?.name ?? '')
  const [email] = useState(user?.email ?? 'founder@autofounder.ai')
  const [showApiKey, setShowApiKey] = useState(false)
  const [saved, setSaved] = useState(false)

  const MOCK_API_KEY = 'af-sk-prod-c9d3e8f1a2b4d5e6f7a8b9c0d1e2f3a4'

  function handleSave() {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function handleCopyKey() {
    navigator.clipboard.writeText(MOCK_API_KEY).catch(() => {})
  }

  return (
    <div className="flex flex-col">
      <Header title="Settings" />
      <div className="flex-1 space-y-6 p-6">
        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>Manage your personal information.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  disabled
                  className="cursor-not-allowed"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Organization</Label>
              <Input value="Euron AutoFounder AI" disabled className="cursor-not-allowed" />
            </div>
            <Button onClick={handleSave} className="gap-1.5">
              <Save className="h-4 w-4" />
              {saved ? 'Saved!' : 'Save Changes'}
            </Button>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
            <CardDescription>
              Use these keys to call the AutoFounder API from external systems.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5">
              <Label>Production API Key</Label>
              <div className="flex gap-2">
                <Input
                  type={showApiKey ? 'text' : 'password'}
                  value={MOCK_API_KEY}
                  readOnly
                  className="font-mono text-xs"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
                <Button variant="outline" size="icon" onClick={handleCopyKey}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Never expose this key in client-side code. Rotate it immediately if compromised.
            </p>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>Control when AutoFounder notifies you.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: 'HITL gate awaiting review', on: true },
              { label: 'Run completed successfully', on: true },
              { label: 'Deployment failed', on: true },
              { label: 'Weekly usage digest', on: false },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm">{item.label}</span>
                <div
                  className={`h-5 w-9 cursor-pointer rounded-full transition-colors ${item.on ? 'bg-primary' : 'bg-muted'}`}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        <Separator />

        {/* Danger Zone */}
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-4 w-4" />
              Danger Zone
            </CardTitle>
            <CardDescription>Irreversible account actions.</CardDescription>
          </CardHeader>
          <CardContent>
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="destructive" className="gap-1.5">
                  <Trash2 className="h-4 w-4" />
                  Delete Account
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Are you absolutely sure?</DialogTitle>
                  <DialogDescription>
                    This will permanently delete your account, all runs, generated code, and
                    deployed products. This action cannot be undone.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button variant="outline">Cancel</Button>
                  <Button variant="destructive">Yes, Delete Everything</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
