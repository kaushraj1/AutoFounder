import React from "react";
import { Text, View } from "react-native";
import type { RunStatus } from "../lib/store";

interface StatusBadgeProps {
  status: RunStatus;
}

const STATUS_CONFIG: Record<RunStatus, { label: string; className: string; textClass: string }> = {
  pending: {
    label: "Pending",
    className: "bg-yellow-500/20 border border-yellow-500/40",
    textClass: "text-yellow-400",
  },
  active: {
    label: "Active",
    className: "bg-blue-500/20 border border-blue-500/40",
    textClass: "text-blue-400",
  },
  complete: {
    label: "Complete",
    className: "bg-green-500/20 border border-green-500/40",
    textClass: "text-green-400",
  },
  failed: {
    label: "Failed",
    className: "bg-red-500/20 border border-red-500/40",
    textClass: "text-red-400",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return (
    <View className={`px-2 py-0.5 rounded-full ${config.className}`}>
      <Text className={`text-xs font-semibold ${config.textClass}`}>{config.label}</Text>
    </View>
  );
}
