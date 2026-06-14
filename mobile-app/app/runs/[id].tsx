import { useLocalSearchParams, useRouter } from "expo-router";
import { ScrollView, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { StatusBadge } from "../../components/StatusBadge";
import type { RunStatus } from "../../lib/store";

const PILLARS = [
  { number: 1, name: "Strategy", emoji: "🎯" },
  { number: 2, name: "Research", emoji: "🔬" },
  { number: 3, name: "Product Plan", emoji: "📋" },
  { number: 4, name: "Engineering", emoji: "⚙️" },
  { number: 5, name: "Reviewer", emoji: "🔍" },
  { number: 6, name: "DevOps", emoji: "🚀" },
  { number: 7, name: "LLMOps", emoji: "🧠" },
];

const MOCK_RUN = {
  id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  idea: "AI-powered legal document drafting for freelancers — generate NDAs, contracts, and invoices in seconds",
  status: "active" as RunStatus,
  currentPillar: 4,
  organizationId: "org-1",
  createdAt: "2026-06-14T09:00:00Z",
};

function PillarStep({
  pillar,
  currentPillar,
}: {
  pillar: (typeof PILLARS)[number];
  currentPillar: number;
}) {
  const done = pillar.number < currentPillar;
  const active = pillar.number === currentPillar;
  const pending = pillar.number > currentPillar;

  return (
    <View className="flex-row items-center gap-3 py-3 border-b border-slate-800">
      <View
        className={`w-9 h-9 rounded-full items-center justify-center ${
          done
            ? "bg-green-500/20 border border-green-500/40"
            : active
              ? "bg-brand-500/20 border border-brand-500/40"
              : "bg-slate-800 border border-slate-700"
        }`}
      >
        {done ? (
          <Text className="text-green-400 text-sm">✓</Text>
        ) : (
          <Text className="text-base">{pillar.emoji}</Text>
        )}
      </View>
      <View className="flex-1">
        <Text
          className={`text-sm font-semibold ${
            done
              ? "text-green-400"
              : active
                ? "text-brand-300"
                : pending
                  ? "text-slate-500"
                  : "text-slate-300"
          }`}
        >
          Pillar {pillar.number} — {pillar.name}
        </Text>
        <Text className="text-slate-500 text-xs mt-0.5">
          {done ? "Complete" : active ? "In progress…" : "Waiting"}
        </Text>
      </View>
      {active && (
        <View className="bg-brand-500/20 border border-brand-500/40 rounded-full px-2 py-0.5">
          <Text className="text-brand-400 text-xs font-semibold">Active</Text>
        </View>
      )}
    </View>
  );
}

export default function RunDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  // Use mock data; in production this would be a query
  const run = { ...MOCK_RUN, id: id ?? MOCK_RUN.id };

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      {/* Back header */}
      <View className="flex-row items-center px-5 pt-3 pb-2 border-b border-slate-800">
        <TouchableOpacity
          className="mr-3 p-1"
          onPress={() => router.back()}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Text className="text-brand-400 text-base">← Back</Text>
        </TouchableOpacity>
        <Text className="text-slate-100 font-semibold text-base flex-1" numberOfLines={1}>
          Run #{run.id.slice(0, 8)}
        </Text>
        <StatusBadge status={run.status} />
      </View>

      <ScrollView className="flex-1" contentContainerStyle={{ padding: 20 }}>
        {/* Idea card */}
        <View className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-5">
          <Text className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-1.5">
            Idea
          </Text>
          <Text className="text-slate-100 text-sm leading-6">{run.idea}</Text>
        </View>

        {/* HITL button if active */}
        {run.status === "active" && (
          <TouchableOpacity
            className="bg-brand-500 rounded-xl py-3.5 items-center mb-5"
            onPress={() => router.push(`/runs/${run.id}/hitl`)}
            activeOpacity={0.85}
          >
            <Text className="text-white font-semibold text-sm">Review & Approve Gate</Text>
          </TouchableOpacity>
        )}

        {/* Pillar progress */}
        <Text className="text-slate-100 text-base font-semibold mb-2">Pillar Progress</Text>
        <View className="bg-slate-800 border border-slate-700 rounded-xl px-4 mb-5">
          {PILLARS.map((p) => (
            <PillarStep key={p.number} pillar={p} currentPillar={run.currentPillar} />
          ))}
        </View>

        {/* Meta */}
        <View className="bg-slate-800 border border-slate-700 rounded-xl p-4">
          <Text className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-3">
            Details
          </Text>
          <View className="gap-2">
            <View className="flex-row justify-between">
              <Text className="text-slate-400 text-sm">Run ID</Text>
              <Text className="text-slate-300 text-xs font-mono">{run.id.slice(0, 16)}…</Text>
            </View>
            <View className="flex-row justify-between">
              <Text className="text-slate-400 text-sm">Created</Text>
              <Text className="text-slate-300 text-sm">
                {new Date(run.createdAt).toLocaleDateString()}
              </Text>
            </View>
            <View className="flex-row justify-between">
              <Text className="text-slate-400 text-sm">Organization</Text>
              <Text className="text-slate-300 text-sm">{run.organizationId}</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
