'use client'

import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? 'https://scfwpiogcuxzsgdgnslt.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjZndwaW9nY3V4enNnZGduc2x0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE0MjAzMjEsImV4cCI6MjA5Njk5NjMyMX0.fESbMaqD_lo2qqrvFo4viLLWF9_irlrDRhxZtFCNZ3U'

export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)
