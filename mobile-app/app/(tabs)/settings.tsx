import { Alert, ScrollView, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { supabase } from "../../lib/supabase";
import { useAppStore } from "../../lib/store";

function SettingsRow({
  label,
  value,
  onPress,
  danger,
}: {
  label: string;
  value?: string;
  onPress?: () => void;
  danger?: boolean;
}) {
  return (
    <TouchableOpacity
      className="flex-row items-center justify-between py-3.5 border-b border-slate-800"
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={onPress ? 0.7 : 1}
    >
      <Text className={`text-sm font-medium ${danger ? "text-red-400" : "text-slate-300"}`}>
        {label}
      </Text>
      {value ? (
        <Text className="text-slate-500 text-sm font-mono">{value}</Text>
      ) : null}
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const user = useAppStore((s) => s.user);
  const displayName = user?.email?.split("@")[0] ?? "Founder";
  const maskedKey = "sk-af-••••••••••••••••3a9f";

  async function handleLogout() {
    Alert.alert("Sign out", "Are you sure you want to sign out?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Sign out",
        style: "destructive",
        onPress: async () => {
          await supabase.auth.signOut();
        },
      },
    ]);
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <ScrollView className="flex-1" contentContainerStyle={{ padding: 20 }}>
        <Text className="text-slate-100 text-2xl font-bold mb-6">Settings</Text>

        {/* Profile section */}
        <View className="bg-slate-800 border border-slate-700 rounded-xl p-4 mb-5 items-center">
          <View className="w-16 h-16 rounded-full bg-brand-500 items-center justify-center mb-3">
            <Text className="text-white text-2xl font-bold uppercase">
              {displayName.charAt(0)}
            </Text>
          </View>
          <Text className="text-slate-100 text-base font-semibold capitalize">{displayName}</Text>
          <Text className="text-slate-400 text-sm mt-0.5">{user?.email ?? "—"}</Text>
          <View className="bg-brand-500/20 border border-brand-500/40 rounded-full px-3 py-1 mt-2">
            <Text className="text-brand-400 text-xs font-semibold">Pro Plan</Text>
          </View>
        </View>

        {/* Account section */}
        <Text className="text-slate-500 text-xs font-semibold uppercase tracking-widest mb-2">
          Account
        </Text>
        <View className="bg-slate-800 border border-slate-700 rounded-xl px-4 mb-5">
          <SettingsRow label="Email" value={user?.email ?? "—"} />
          <SettingsRow label="Plan" value="Pro" />
          <SettingsRow label="Organization" value="euron-demo" />
        </View>

        {/* API section */}
        <Text className="text-slate-500 text-xs font-semibold uppercase tracking-widest mb-2">
          API
        </Text>
        <View className="bg-slate-800 border border-slate-700 rounded-xl px-4 mb-5">
          <SettingsRow label="API Key" value={maskedKey} />
          <SettingsRow
            label="Regenerate API Key"
            onPress={() => Alert.alert("Coming soon", "Key regeneration available in v1.1")}
          />
        </View>

        {/* Preferences section */}
        <Text className="text-slate-500 text-xs font-semibold uppercase tracking-widest mb-2">
          Preferences
        </Text>
        <View className="bg-slate-800 border border-slate-700 rounded-xl px-4 mb-5">
          <SettingsRow
            label="Push Notifications"
            value="Enabled"
            onPress={() => Alert.alert("Coming soon", "Notification settings in v1.1")}
          />
          <SettingsRow label="App Version" value="1.0.0" />
        </View>

        {/* Danger zone */}
        <View className="bg-slate-800 border border-slate-700 rounded-xl px-4 mb-8">
          <SettingsRow label="Sign out" danger onPress={handleLogout} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
