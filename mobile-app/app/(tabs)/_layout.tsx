import { Tabs } from "expo-router";
import { Text } from "react-native";
import { useAppStore } from "../../lib/store";

function TabIcon({ label, emoji }: { label: string; emoji: string }) {
  return (
    <Text className="text-xl" accessibilityLabel={label}>
      {emoji}
    </Text>
  );
}

export default function TabsLayout() {
  const unreadCount = useAppStore((s) => s.unreadCount);

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: "#1e293b",
          borderTopColor: "#334155",
          borderTopWidth: 1,
        },
        tabBarActiveTintColor: "#38bdf8",
        tabBarInactiveTintColor: "#64748b",
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Dashboard",
          tabBarIcon: ({ focused }) => (
            <TabIcon label="Dashboard" emoji={focused ? "🏠" : "🏠"} />
          ),
        }}
      />
      <Tabs.Screen
        name="runs"
        options={{
          title: "Runs",
          tabBarIcon: ({ focused }) => (
            <TabIcon label="Runs" emoji={focused ? "⚡" : "⚡"} />
          ),
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: "Alerts",
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
          tabBarIcon: ({ focused }) => (
            <TabIcon label="Notifications" emoji={focused ? "🔔" : "🔔"} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: "Settings",
          tabBarIcon: ({ focused }) => (
            <TabIcon label="Settings" emoji={focused ? "⚙️" : "⚙️"} />
          ),
        }}
      />
    </Tabs>
  );
}
