import { FlatList, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAppStore, type Notification } from "../../lib/store";

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: "n1",
    title: "Strategy complete",
    body: "Run a1b2c3d4 — Strategy Agent finished. Ready for your review.",
    read: false,
    createdAt: "2026-06-14T09:45:00Z",
  },
  {
    id: "n2",
    title: "Deploy succeeded",
    body: 'Run b2c3d4e5 — Your product "SubscribeIQ" is now live at subscribeiq.euron.one',
    read: false,
    createdAt: "2026-06-12T18:00:00Z",
  },
  {
    id: "n3",
    title: "Review failed",
    body: "Run d4e5f6a7 — Reviewer Agent flagged 3 critical issues. Action required.",
    read: true,
    createdAt: "2026-06-11T10:20:00Z",
  },
  {
    id: "n4",
    title: "HITL gate waiting",
    body: "Run a1b2c3d4 — Architecture plan ready. Approve to continue to Pillar 3.",
    read: false,
    createdAt: "2026-06-14T11:30:00Z",
  },
  {
    id: "n5",
    title: "LLMOps report ready",
    body: "Weekly LLMOps analysis complete. Potential savings: $0.42. View report.",
    read: true,
    createdAt: "2026-06-13T07:00:00Z",
  },
];

function NotificationItem({ item }: { item: Notification }) {
  const date = new Date(item.createdAt).toLocaleDateString("en-IN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <View
      className={`p-4 border-b border-slate-800 ${item.read ? "opacity-60" : ""}`}
    >
      <View className="flex-row items-start gap-3">
        {!item.read && (
          <View className="w-2 h-2 rounded-full bg-brand-400 mt-1.5 shrink-0" />
        )}
        {item.read && <View className="w-2 h-2 shrink-0" />}
        <View className="flex-1">
          <Text className="text-slate-100 text-sm font-semibold mb-0.5">{item.title}</Text>
          <Text className="text-slate-400 text-sm leading-5">{item.body}</Text>
          <Text className="text-slate-600 text-xs mt-1.5">{date}</Text>
        </View>
      </View>
    </View>
  );
}

export default function NotificationsScreen() {
  const markAllRead = useAppStore((s) => s.markAllRead);

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <View className="flex-row items-center justify-between px-5 pt-4 pb-3">
        <Text className="text-slate-100 text-2xl font-bold">Notifications</Text>
        <TouchableOpacity
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5"
          onPress={markAllRead}
        >
          <Text className="text-slate-300 text-xs font-medium">Mark all read</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={MOCK_NOTIFICATIONS}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <NotificationItem item={item} />}
        contentContainerStyle={{ paddingBottom: 32 }}
        ListEmptyComponent={
          <View className="items-center py-16">
            <Text className="text-slate-500 text-base">No notifications yet</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}
