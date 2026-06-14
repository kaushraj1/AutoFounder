import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Run, User } from './types'

interface AppStore {
  currentRun: Run | null
  setCurrentRun: (run: Run | null) => void
  user: User | null
  setUser: (user: User | null) => void
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      currentRun: null,
      setCurrentRun: (run) => set({ currentRun: run }),
      user: null,
      setUser: (user) => set({ user }),
      sidebarOpen: true,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: 'autofounder-app-store',
      partialize: (state) => ({ user: state.user, sidebarOpen: state.sidebarOpen }),
    }
  )
)
