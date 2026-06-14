import { create } from "zustand";
import type { Session, User } from "@supabase/supabase-js";

export type RunStatus = "pending" | "active" | "complete" | "failed";

export interface Run {
  id: string;
  idea: string;
  status: RunStatus;
  currentPillar: number;
  createdAt: string;
  organizationId: string;
}

export interface Notification {
  id: string;
  title: string;
  body: string;
  read: boolean;
  createdAt: string;
}

interface AuthState {
  session: Session | null;
  user: User | null;
  setSession: (session: Session | null) => void;
}

interface RunsState {
  runs: Run[];
  setRuns: (runs: Run[]) => void;
  addRun: (run: Run) => void;
  updateRun: (id: string, patch: Partial<Run>) => void;
}

interface NotificationsState {
  notifications: Notification[];
  unreadCount: number;
  setNotifications: (notifications: Notification[]) => void;
  markAllRead: () => void;
}

type AppStore = AuthState & RunsState & NotificationsState;

export const useAppStore = create<AppStore>((set) => ({
  // Auth
  session: null,
  user: null,
  setSession: (session) =>
    set({ session, user: session?.user ?? null }),

  // Runs
  runs: [],
  setRuns: (runs) => set({ runs }),
  addRun: (run) => set((state) => ({ runs: [run, ...state.runs] })),
  updateRun: (id, patch) =>
    set((state) => ({
      runs: state.runs.map((r) => (r.id === id ? { ...r, ...patch } : r)),
    })),

  // Notifications
  notifications: [],
  unreadCount: 0,
  setNotifications: (notifications) =>
    set({
      notifications,
      unreadCount: notifications.filter((n) => !n.read).length,
    }),
  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),
}));
