import { useState } from "react";
import { FlatList, Text, TextInput, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { RunCard } from "../../components/RunCard";
import { type Run, type RunStatus } from "../../lib/store";

const MOCK_RUNS: Run[] = [
  {
    id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    idea: "AI-powered legal document drafting for freelancers",
    status: "active",
    currentPillar: 4,
    createdAt: "2026-06-14T09:00:00Z",
    organizationId: "org-1",
  },
  {
    id: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    idea: "Subscription analytics SaaS for indie makers",
    status: "complete",
    currentPillar: 7,
    createdAt: "2026-06-12T14:30:00Z",
    organizationId: "org-1",
  },
  {
    id: "c3d4e5f6-a7b8-9012-cdef-123456789012",
    idea: "Async standup tool for remote engineering teams",
    status: "pending",
    currentPillar: 1,
    createdAt: "2026-06-13T11:00:00Z",
    organizationId: "org-1",
  },
  {
    id: "d4e5f6a7-b8c9-0123-defa-234567890123",
    idea: "B2B cold outreach personalisation engine",
    status: "failed",
    currentPillar: 2,
    createdAt: "2026-06-11T08:00:00Z",
    organizationId: "org-1",
  },
];

type FilterOption = "all" | RunStatus;
const FILTERS: { key: FilterOption; label: string }[] = [
  { key: "all", label: "All" },
  { key: "active", label: "Active" },
  { key: "complete", label: "Complete" },
  { key: "pending", label: "Pending" },
  { key: "failed", label: "Failed" },
];

export default function RunsScreen() {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterOption>("all");

  const filtered = MOCK_RUNS.filter((run) => {
    const matchesFilter = activeFilter === "all" || run.status === activeFilter;
    const matchesSearch =
      search.trim() === "" ||
      run.idea.toLowerCase().includes(search.toLowerCase()) ||
      run.id.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <View className="px-5 pt-4 pb-2">
        <Text className="text-slate-100 text-2xl font-bold mb-4">Runs</Text>

        {/* Search bar */}
        <TextInput
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-xl px-4 py-3 text-sm mb-3"
          placeholder="Search by idea or run ID..."
          placeholderTextColor="#64748b"
          value={search}
          onChangeText={setSearch}
          autoCapitalize="none"
        />

        {/* Filter chips */}
        <View className="flex-row gap-2 flex-wrap">
          {FILTERS.map((f) => (
            <TouchableOpacity
              key={f.key}
              className={`px-3 py-1.5 rounded-full border ${
                activeFilter === f.key
                  ? "bg-brand-500 border-brand-500"
                  : "bg-transparent border-slate-700"
              }`}
              onPress={() => setActiveFilter(f.key)}
            >
              <Text
                className={`text-xs font-semibold ${
                  activeFilter === f.key ? "text-white" : "text-slate-400"
                }`}
              >
                {f.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <RunCard run={item} />}
        contentContainerStyle={{ paddingHorizontal: 20, paddingTop: 12, paddingBottom: 32 }}
        ListEmptyComponent={
          <View className="items-center py-16">
            <Text className="text-slate-500 text-base">No runs found</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}
