import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";
import "../global.css";
import { supabase } from "../lib/supabase";
import { useAppStore } from "../lib/store";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30_000,
    },
  },
});

function AuthGate({ children }: { children: React.ReactNode }) {
  const setSession = useAppStore((s) => s.setSession);
  const session = useAppStore((s) => s.session);
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => listener.subscription.unsubscribe();
  }, [setSession]);

  useEffect(() => {
    const inAuthGroup = segments[0] === "(auth)";
    if (!session && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (session && inAuthGroup) {
      router.replace("/(tabs)");
    }
  }, [session, segments, router]);

  return <>{children}</>;
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <AuthGate>
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(tabs)" />
            <Stack.Screen
              name="new-idea"
              options={{
                presentation: "modal",
                headerShown: true,
                headerTitle: "New Idea",
                headerStyle: { backgroundColor: "#0f172a" },
                headerTintColor: "#f1f5f9",
              }}
            />
            <Stack.Screen
              name="monitoring"
              options={{
                headerShown: true,
                headerTitle: "Monitoring",
                headerStyle: { backgroundColor: "#0f172a" },
                headerTintColor: "#f1f5f9",
              }}
            />
            <Stack.Screen name="runs/[id]" />
          </Stack>
        </AuthGate>
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}
