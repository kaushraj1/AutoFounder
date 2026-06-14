import { useState } from "react";
import { RefreshControl, ScrollView, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

interface UrlHealthCard {
  url: string;
  label: string;
  status: "healthy" | "degraded" | "down";
  latencyMs: number;
  checkedAt: string;
}

interface DriftAlertCard {
  agentId: string;
  metric: string;
  driftPct: number;
  severity: "warning" | "critical";
}

const MOCK_HEALTH: UrlHealthCard[] = [
  {
    url: "https://api.euron.one/health",
    label: "API Gateway",
    status: "healthy",
    latencyMs: 42,
    checkedAt: "2026-06-14T12:00:00Z",
  },
  {
    url: "https://subscribeiq.euron.one",
    label: "SubscribeIQ (prod)",
    status: "healthy",
    latencyMs: 118,
    checkedAt: "2026-06-14T12:00:00Z",
  },
  {
    url: "https://legalbot.euron.one",
    label: "LegalBot (prod)",
    status: "degraded",
    latencyMs: 890,
    checkedAt: "2026-06-14T12:00:00Z",
  },
];

const MOCK_DRIFT: DriftAlertCard[] = [
  {
    agentId: "reviewer",
    metric: "verify_pass_rate",
    driftPct: 28.5,
    severity: "critical",
  },
  {
    agentId: "strategy",
    metric: "avg_tokens",
    driftPct: 14.2,
    severity: "warning",
  },
];

const STATUS_CONFIG = {
  healthy: { label: "Healthy", dotClass: "bg-green-400", textClass: "text-green-400" },
  degraded: { label: "Degraded", dotClass: "bg-yellow-400", textClass: "text-yellow-400" },
  down: { label: "Down", dotClass: "bg-red-400", textClass: "text-red-400" },
};

function HealthCard({ item }: { item: UrlHealthCard }) {
  const cfg = STATUS_CONFIG[item.status];
  return (
    <View className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-3">
      <View className="flex-row items-center justify-between mb-1">
        <Text className="text-slate-100 text-sm font-semibold">{item.label}</Text>
        <View className="flex-row items-center gap-1.5">
          <View className={`w-2 h-2 rounded-full ${cfg.dotClass}`} />
          <Text className={`text-xs font-semibold ${cfg.textClass}`}>{cfg.label}</Text>
        </View>
      </View>
      <Text className="text-slate-500 text-xs font-mono" numberOfLines={1}>
        {item.url}
      </Text>
      <Text className="text-slate-400 text-xs mt-1.5">Latency: {item.latencyMs} ms</Text>
    </View>
  );
}

function DriftCard({ item }: { item: DriftAlertCard }) {
  const critical = item.severity === "critical";
  return (
    <View
      className={`rounded-xl p-4 mb-3 border ${
        critical
          ? "bg-red-500/10 border-red-500/30"
          : "bg-yellow-500/10 border-yellow-500/30"
      }`}
    >
      <View className="flex-row items-center justify-between">
        <Text className="text-slate-100 text-sm font-semibold">{item.agentId}</Text>
        <View
          className={`rounded-full px-2 py-0.5 border ${
            critical
              ? "bg-red-500/20 border-red-500/40"
              : "bg-yellow-500/20 border-yellow-500/40"
          }`}
        >
          <Text className={`text-xs font-semibold ${critical ? "text-red-400" : "text-yellow-400"}`}>
            {item.severity.toUpperCase()}
          </Text>
        </View>
      </View>
      <Text className="text-slate-400 text-xs mt-1.5">
        {item.metric} drifted by{" "}
        <Text className={critical ? "text-red-300" : "text-yellow-300"}>
          {item.driftPct.toFixed(1)}%
        </Text>{" "}
        from baseline
      </Text>
    </View>
  );
}

export default function MonitoringScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  function onRefresh() {
    setRefreshing(true);
    setTimeout(() => {
      setLastRefresh(new Date());
      setRefreshing(false);
    }, 1200);
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950" edges={["bottom"]}>
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 20 }}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#38bdf8"
          />
        }
      >
        {/* Header row */}
        <View className="flex-row items-center justify-between mb-5">
          <View>
            <Text className="text-slate-400 text-xs">Last updated</Text>
            <Text className="text-slate-300 text-sm font-mono">
              {lastRefresh.toLocaleTimeString()}
            </Text>
          </View>
          <TouchableOpacity
            className="bg-brand-500/20 border border-brand-500/40 rounded-lg px-3 py-1.5"
            onPress={onRefresh}
          >
            <Text className="text-brand-400 text-sm font-semibold">Refresh</Text>
          </TouchableOpacity>
        </View>

        {/* Cost meter */}
        <View className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-5">
          <Text className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-3">
            Monthly Cost
          </Text>
          <View className="flex-row items-end gap-2 mb-2">
            <Text className="text-slate-100 text-3xl font-bold">$0.84</Text>
            <Text className="text-slate-400 text-sm mb-1">/ $10 budget</Text>
          </View>
          <View className="bg-slate-700 rounded-full h-2 overflow-hidden">
            <View className="bg-brand-500 h-2 rounded-full" style={{ width: "8.4%" }} />
          </View>
          <Text className="text-slate-500 text-xs mt-1.5">8.4% of monthly budget used</Text>
        </View>

        {/* URL Health */}
        <Text className="text-slate-100 text-base font-semibold mb-3">Live URL Health</Text>
        {MOCK_HEALTH.map((item) => (
          <HealthCard key={item.url} item={item} />
        ))}

        {/* Drift Alerts */}
        <Text className="text-slate-100 text-base font-semibold mt-3 mb-3">Drift Alerts</Text>
        {MOCK_DRIFT.length === 0 ? (
          <View className="bg-slate-800 border border-slate-700 rounded-xl p-4 items-center">
            <Text className="text-green-400 text-sm font-medium">All metrics within baseline</Text>
          </View>
        ) : (
          MOCK_DRIFT.map((item, idx) => <DriftCard key={idx} item={item} />)
        )}

        <View className="h-6" />
      </ScrollView>
    </SafeAreaView>
  );
}
