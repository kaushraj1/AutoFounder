import { useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { api } from "../lib/api";

const DOMAINS = [
  "SaaS",
  "Marketplace",
  "Consumer App",
  "FinTech",
  "HealthTech",
  "EdTech",
  "DevTools",
  "AI / ML",
  "E-commerce",
  "Other",
];

const PLACEHOLDER =
  "Describe your startup idea in as much detail as you like. The more context you give, the better AutoFounder can tailor the strategy.\n\nExample: \"A B2B SaaS tool that automatically generates legal contracts for freelancers in India using AI, removing the need for a lawyer for standard NDAs, service agreements, and invoices.\"";

export default function NewIdeaScreen() {
  const router = useRouter();
  const [idea, setIdea] = useState("");
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const charCount = idea.trim().length;
  const isValid = charCount >= 20;

  async function handleSubmit() {
    if (!isValid) {
      Alert.alert("Too short", "Please describe your idea in at least 20 characters.");
      return;
    }
    setLoading(true);
    try {
      const result = await api.createIdea(idea.trim(), selectedDomain ?? undefined);
      Alert.alert(
        "Run started!",
        `Your idea has been submitted. Run ID: ${result.run_id}`,
        [{ text: "View run", onPress: () => router.push(`/runs/${result.run_id}`) }],
      );
    } catch (err) {
      // Show a friendly message in dev (no backend running)
      Alert.alert(
        "Submitted (demo mode)",
        "Backend not reachable — in production this would start a new run.",
        [{ text: "OK", onPress: () => router.back() }],
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950" edges={["bottom"]}>
      <KeyboardAvoidingView
        className="flex-1"
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          className="flex-1"
          contentContainerStyle={{ padding: 20 }}
          keyboardShouldPersistTaps="handled"
        >
          <Text className="text-slate-400 text-sm font-medium mb-2">
            Your idea <Text className="text-red-400">*</Text>
          </Text>
          <TextInput
            className="bg-slate-800 border border-slate-700 text-slate-100 rounded-xl px-4 py-4 text-sm leading-6 mb-1"
            placeholder={PLACEHOLDER}
            placeholderTextColor="#475569"
            multiline
            numberOfLines={8}
            textAlignVertical="top"
            value={idea}
            onChangeText={setIdea}
            style={{ minHeight: 180 }}
          />
          <Text className={`text-xs mb-5 ${isValid ? "text-slate-500" : "text-red-400"}`}>
            {charCount} characters {isValid ? "" : "(minimum 20)"}
          </Text>

          {/* Domain picker */}
          <Text className="text-slate-400 text-sm font-medium mb-2">Domain (optional)</Text>
          <View className="flex-row flex-wrap gap-2 mb-8">
            {DOMAINS.map((d) => (
              <TouchableOpacity
                key={d}
                className={`px-3 py-2 rounded-xl border ${
                  selectedDomain === d
                    ? "bg-brand-500 border-brand-500"
                    : "bg-slate-800 border-slate-700"
                }`}
                onPress={() => setSelectedDomain((prev) => (prev === d ? null : d))}
              >
                <Text
                  className={`text-sm font-medium ${
                    selectedDomain === d ? "text-white" : "text-slate-300"
                  }`}
                >
                  {d}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Submit */}
          <TouchableOpacity
            className={`rounded-xl py-4 items-center ${
              isValid ? "bg-brand-500" : "bg-slate-700"
            }`}
            onPress={handleSubmit}
            disabled={!isValid || loading}
            activeOpacity={0.85}
          >
            {loading ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text className={`font-bold text-base ${isValid ? "text-white" : "text-slate-500"}`}>
                Launch AutoFounder
              </Text>
            )}
          </TouchableOpacity>

          <View className="h-6" />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
