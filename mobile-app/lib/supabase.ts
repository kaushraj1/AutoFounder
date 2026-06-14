import AsyncStorage from "@react-native-async-storage/async-storage";
import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL ?? "https://scfwpiogcuxzsgdgnslt.supabase.co";
const SUPABASE_ANON_KEY =
  process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ??
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjZndwaW9nY3V4enNnZGduc2x0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE0MjAzMjEsImV4cCI6MjA5Njk5NjMyMX0.fESbMaqD_lo2qqrvFo4viLLWF9_irlrDRhxZtFCNZ3U";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
