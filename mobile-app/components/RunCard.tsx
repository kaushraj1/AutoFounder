import { useRouter } from "expo-router";
import React from "react";
import { Text, TouchableOpacity, View } from "react-native";
import type { Run } from "../lib/store";
import { StatusBadge } from "./StatusBadge";

const TOTAL_PILLARS = 7;

interface RunCardProps {
  run: Run;
}

export function RunCard({ run }: RunCardProps) {
  const router = useRouter();
  const shortId = run.id.slice(0, 8);
  const ideaPreview =
    run.idea.length > 80 ? `${run.idea.slice(0, 80)}…` : run.idea;

  return (
    <TouchableOpacity
      className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-3"
      onPress={() => router.push(`/runs/${run.id}`)}
      activeOpacity={0.7}
    >
      {/* Header row */}
      <View className="flex-row items-center justify-between mb-2">
        <Text className="text-slate-400 text-xs font-mono">#{shortId}</Text>
        <StatusBadge status={run.status} />
      </View>

      {/* Idea text */}
      <Text className="text-slate-100 text-sm font-medium leading-5 mb-3">
        {ideaPreview}
      </Text>

      {/* Pillar progress bar */}
      <View className="flex-row gap-1">
        {Array.from({ length: TOTAL_PILLARS }).map((_, i) => {
          const filled = i < run.currentPillar;
          const active = i === run.currentPillar - 1 && run.status === "active";
          return (
            <View
              key={i}
              className={`h-1.5 flex-1 rounded-full ${
                filled
                  ? active
                    ? "bg-brand-400"
                    : "bg-brand-600"
                  : "bg-slate-700"
              }`}
            />
          );
        })}
      </View>
      <Text className="text-slate-500 text-xs mt-1.5">
        Pillar {run.currentPillar} / {TOTAL_PILLARS}
      </Text>
    </TouchableOpacity>
  );
}
