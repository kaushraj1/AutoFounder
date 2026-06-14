import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { ScrollView, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { RunCard } from "../../components/RunCard";
import { api } from "../../lib/api";
import { useAppStore, type Run } from "../../lib/store";

const MOCK_RUNS: Run[] = [
  {
    id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    idea: "AI-powered legal document drafting for freelancers — generate NDAs, contracts, and invoices in seconds",
    status: "active",
    currentPillar: 4,
    createdAt: "2026-06-14T09:00:00Z",
    organizationId: "org-1",
  },
  {
    id: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    idea: "Subscription analytics SaaS for indie makers — track MRR, churn, and LTV without spreadsheets",
    status: "complete",
    currentPillar: 7,
    createdAt: "2026-06-12T14:30:00Z",
    organizationId: "org-1",
  },
  {
    id: "c3d4e5f6-a7b8-9012-cdef-123456789012",
    idea: "Async standup tool for remote engineering teams with AI-generated summaries",
    status: "pending",
    currentPillar: 1,
    createdAt: "2026-06-13T11:00:00Z",
    organizationId: "org-1",
  },
];

interface StatCardProps {
  label: string;
  value: string | number;
  accent?: boolean;
}

function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <View className="flex-1 bg-slate-800 border border-slate-700 rounded-xl p-3.5 items-center">
      <Text className={`text-2xl font-bold ${accent ? "text-brand-400" : "text-slate-100"}`}>
        {value}
      </Text>
      <Text className="text-slate-400 text-xs mt-0.5 text-center">{label}</Text>
    </View>
  );
}

export default function DashboardScreen() {
  const router = useRouter();
  const user = useAppStore((s) => s.user);
  const { data: runsData } = useQuery({
    queryKey: ["runs"],
    queryFn: api.getRuns,
    enabled: false, // use mock data for now
  });

  const runs = (runsData as { items: Run[] } | undefined)?.items ?? MOCK_RUNS;
  const activeRuns = runs.filter((r) => r.status === "active").length;
  const completeRuns = runs.filter((r) => r.status === "complete").length;

  const displayName = user?.email?.split("@")[0] ?? "Founder";

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <ScrollView className="flex-1" contentContainerStyle={{ padding: 20 }}>
        {/* Header */}
        <View className="flex-row items-center justify-between mb-6">
          <View>
            <Text className="text-slate-400 text-sm">Welcome back,</Text>
            <Text className="text-slate-100 text-xl font-bold capitalize">{displayName}</Text>
          </View>
          <TouchableOpacity
            className="bg-slate-800 border border-slate-700 rounded-full w-10 h-10 items-center justify-center"
            onPress={() => router.push("/monitoring")}
          >
            <Text className="text-base">📡</Text>
          </TouchableOpacity>
        </View>

        {/* Stats row */}
        <View className="flex-row gap-3 mb-6">
          <StatCard label="Active Runs" value={activeRuns} accent />
          <StatCard label="Live Products" value={completeRuns} />
          <StatCard label="Tokens Today" value="48K" />
        </View>

        {/* Recent Runs heading */}
        <View className="flex-row items-center justify-between mb-3">
          <Text className="text-slate-100 text-base font-semibold">Recent Runs</Text>
          <TouchableOpacity onPress={() => router.push("/(tabs)/runs")}>
            <Text className="text-brand-400 text-sm">See all</Text>
          </TouchableOpacity>
        </View>

        {/* Run cards */}
        {runs.slice(0, 5).map((run) => (
          <RunCard key={run.id} run={run} />
        ))}

        {/* Spacer for FAB */}
        <View className="h-24" />
      </ScrollView>

      {/* FAB */}
      <TouchableOpacity
        className="absolute bottom-8 right-6 bg-brand-500 w-14 h-14 rounded-full items-center justify-center shadow-lg"
        onPress={() => router.push("/new-idea")}
        activeOpacity={0.85}
      >
        <Text className="text-white text-3xl font-light leading-none">+</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}
