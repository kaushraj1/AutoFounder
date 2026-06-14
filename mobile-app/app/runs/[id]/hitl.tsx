import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { api } from "../../../lib/api";

const MOCK_GATE = {
  id: "gate-pillar-4-arch",
  title: "Architecture Plan Review",
  description:
    "The Engineering Agent has produced a system architecture plan for your product. Please review the proposed tech stack, database schema, and API surface before proceeding to code generation.",
  pillar: 4,
  items: [
    "Next.js 14 (App Router) frontend + FastAPI backend",
    "PostgreSQL with pgvector for document embeddings",
    "Redis for session caching and job queues",
    "Docker Compose for local dev; ECS Fargate for production",
    "Stripe Billing API integration for subscription management",
  ],
};

export default function HitlScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);

  const gate = MOCK_GATE;

  async function handleDecision(decision: "approve" | "reject") {
    const verb = decision === "approve" ? "Approve" : "Reject";
    Alert.alert(
      `${verb} gate?`,
      decision === "reject"
        ? "Rejecting will pause this run and notify the engineering team."
        : "Approving will continue to the next pillar.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: verb,
          style: decision === "reject" ? "destructive" : "default",
          onPress: async () => {
            setLoading(true);
            try {
              await api.approveGate(id ?? "", gate.id, decision, comment.trim() || undefined);
              Alert.alert("Done", `Gate ${decision}d successfully.`, [
                { text: "OK", onPress: () => router.back() },
              ]);
            } catch (err) {
              Alert.alert("Error", String(err));
            } finally {
              setLoading(false);
            }
          },
        },
      ],
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      {/* Header */}
      <View className="flex-row items-center px-5 pt-3 pb-3 border-b border-slate-800">
        <TouchableOpacity
          className="mr-3"
          onPress={() => router.back()}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Text className="text-brand-400 text-base">← Back</Text>
        </TouchableOpacity>
        <Text className="text-slate-100 font-semibold text-base flex-1">HITL Review</Text>
        <View className="bg-yellow-500/20 border border-yellow-500/40 rounded-full px-2 py-0.5">
          <Text className="text-yellow-400 text-xs font-semibold">Waiting</Text>
        </View>
      </View>

      <ScrollView className="flex-1" contentContainerStyle={{ padding: 20 }}>
        {/* Gate title */}
        <View className="mb-4">
          <Text className="text-slate-400 text-xs uppercase tracking-widest font-semibold mb-1">
            Pillar {gate.pillar} Gate
          </Text>
          <Text className="text-slate-100 text-xl font-bold">{gate.title}</Text>
        </View>

        {/* Description */}
        <View className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-4">
          <Text className="text-slate-300 text-sm leading-6">{gate.description}</Text>
        </View>

        {/* Review items */}
        <Text className="text-slate-100 text-sm font-semibold mb-2">What to review</Text>
        <View className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-5">
          {gate.items.map((item, idx) => (
            <View key={idx} className="flex-row gap-2 mb-2 last:mb-0">
              <Text className="text-brand-400 text-sm font-bold">•</Text>
              <Text className="text-slate-300 text-sm flex-1 leading-5">{item}</Text>
            </View>
          ))}
        </View>

        {/* Optional comment */}
        <Text className="text-slate-400 text-sm font-medium mb-1">Comment (optional)</Text>
        <TextInput
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-xl px-4 py-3 text-sm mb-6"
          placeholder="Add a note for the agent team…"
          placeholderTextColor="#64748b"
          multiline
          numberOfLines={3}
          textAlignVertical="top"
          value={comment}
          onChangeText={setComment}
        />

        {/* Action buttons */}
        {loading ? (
          <ActivityIndicator color="#38bdf8" size="large" />
        ) : (
          <View className="gap-3">
            <TouchableOpacity
              className="bg-green-500 rounded-xl py-4 items-center"
              onPress={() => handleDecision("approve")}
              activeOpacity={0.85}
            >
              <Text className="text-white font-bold text-base">Approve</Text>
            </TouchableOpacity>

            <TouchableOpacity
              className="bg-red-500/20 border border-red-500/40 rounded-xl py-4 items-center"
              onPress={() => handleDecision("reject")}
              activeOpacity={0.85}
            >
              <Text className="text-red-400 font-bold text-base">Reject</Text>
            </TouchableOpacity>
          </View>
        )}

        <View className="h-8" />
      </ScrollView>
    </SafeAreaView>
  );
}
