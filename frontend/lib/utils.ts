import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { RunStatus } from './types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(date))
}

export function formatRelative(date: string | Date): string {
  const now = Date.now()
  const then = new Date(date).getTime()
  const diff = now - then
  const minutes = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days = Math.floor(diff / 86_400_000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

export function statusColor(status: RunStatus): string {
  switch (status) {
    case 'queued':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'running':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'paused':
      return 'bg-orange-100 text-orange-800 border-orange-200'
    case 'completed':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'failed':
      return 'bg-red-100 text-red-800 border-red-200'
    case 'cancelled':
      return 'bg-gray-100 text-gray-700 border-gray-200'
    default:
      return 'bg-gray-100 text-gray-700 border-gray-200'
  }
}

export function pillarLabel(pillar: string): string {
  const labels: Record<string, string> = {
    strategy: 'Strategy',
    research: 'Research',
    product_planner: 'Product Plan',
    engineering: 'Engineering',
    review: 'QA Review',
    devops: 'DevOps',
    marketing: 'Marketing',
    '1': 'Strategy',
    '2': 'Research',
    '3': 'Product Plan',
    '4': 'Engineering',
    '5': 'QA Review',
    '6': 'DevOps',
    '7': 'Marketing',
  }
  return labels[pillar] ?? pillar
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str
  return `${str.slice(0, maxLen)}…`
}
