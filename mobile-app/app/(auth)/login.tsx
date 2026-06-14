import { Link } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { supabase } from "../../lib/supabase";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignIn() {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Error", "Please enter your email and password.");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      Alert.alert("Sign in failed", error.message);
    }
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <KeyboardAvoidingView
        className="flex-1 justify-center px-6"
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        {/* Logo / heading */}
        <View className="mb-10 items-center">
          <Text className="text-brand-400 text-4xl font-bold tracking-tight">AutoFounder</Text>
          <Text className="text-slate-400 text-base mt-2">Your autonomous AI co-founder</Text>
        </View>

        {/* Email */}
        <Text className="text-slate-400 text-sm font-medium mb-1">Email</Text>
        <TextInput
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-xl px-4 py-3.5 text-base mb-4"
          placeholder="you@example.com"
          placeholderTextColor="#64748b"
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
          value={email}
          onChangeText={setEmail}
        />

        {/* Password */}
        <Text className="text-slate-400 text-sm font-medium mb-1">Password</Text>
        <TextInput
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-xl px-4 py-3.5 text-base mb-6"
          placeholder="••••••••"
          placeholderTextColor="#64748b"
          secureTextEntry
          autoComplete="password"
          value={password}
          onChangeText={setPassword}
        />

        {/* Sign in button */}
        <TouchableOpacity
          className="bg-brand-500 rounded-xl py-4 items-center mb-4"
          onPress={handleSignIn}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white font-semibold text-base">Sign in</Text>
          )}
        </TouchableOpacity>

        {/* Sign up link */}
        <View className="flex-row justify-center">
          <Text className="text-slate-400 text-sm">Don&apos;t have an account? </Text>
          <Link href="/(auth)/signup" asChild>
            <TouchableOpacity>
              <Text className="text-brand-400 text-sm font-semibold">Sign up</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
