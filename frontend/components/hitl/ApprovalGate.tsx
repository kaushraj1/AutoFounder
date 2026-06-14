'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
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
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { approveGate } from '@/lib/api-client'

interface ApprovalGateProps {
  runId: string
  gateId: string
  pillarName: string
  onDecision?: (decision: 'approved' | 'rejected', notes?: string) => void
  disabled?: boolean
}

export function ApprovalGate({
  runId,
  gateId,
  pillarName,
  onDecision,
  disabled = false,
}: ApprovalGateProps) {
  const [pending, setPending] = useState<'approve' | 'reject' | null>(null)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleDecision(decision: 'approved' | 'rejected') {
    setLoading(true)
    setError(null)
    try {
      await approveGate(runId, gateId, { decision, notes: notes || undefined })
      onDecision?.(decision, notes || undefined)
      setPending(null)
      setNotes('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-orange-500" />
        <div className="flex-1">
          <p className="font-medium text-orange-900">Human Review Required</p>
          <p className="mt-0.5 text-sm text-orange-700">
            The <strong>{pillarName}</strong> pillar has completed and needs your approval to proceed.
          </p>
          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        {/* Approve */}
        <Dialog open={pending === 'approve'} onOpenChange={(o) => !o && setPending(null)}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              className="gap-1.5 bg-green-600 hover:bg-green-700"
              disabled={disabled}
              onClick={() => setPending('approve')}
            >
              <CheckCircle2 className="h-4 w-4" />
              Approve &amp; Continue
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Approve {pillarName} Output</DialogTitle>
              <DialogDescription>
                This will resume the run and proceed to the next pillar. Add an optional note.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2">
              <Label htmlFor="approve-notes">Notes (optional)</Label>
              <Textarea
                id="approve-notes"
                placeholder="LGTM. Proceed with the proposed architecture..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPending(null)} disabled={loading}>
                Cancel
              </Button>
              <Button
                className="bg-green-600 hover:bg-green-700"
                onClick={() => handleDecision('approved')}
                disabled={loading}
              >
                {loading ? 'Approving...' : 'Confirm Approval'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Reject / Pivot */}
        <Dialog open={pending === 'reject'} onOpenChange={(o) => !o && setPending(null)}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 border-red-200 text-red-700 hover:bg-red-50"
              disabled={disabled}
              onClick={() => setPending('reject')}
            >
              <XCircle className="h-4 w-4" />
              Reject / Pivot
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reject &amp; Request Pivot</DialogTitle>
              <DialogDescription>
                The run will be paused. Describe what to change and the agent will rework this pillar.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2">
              <Label htmlFor="reject-notes">
                Pivot instructions <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="reject-notes"
                placeholder="Change the target segment from SMBs to enterprise. Re-focus the Lean Canvas on..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPending(null)} disabled={loading}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleDecision('rejected')}
                disabled={loading || !notes.trim()}
              >
                {loading ? 'Sending...' : 'Send Pivot Request'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
