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

export default function SignupScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignUp() {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Error", "Please fill in all fields.");
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert("Error", "Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      Alert.alert("Error", "Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) {
      Alert.alert("Sign up failed", error.message);
    } else {
      Alert.alert(
        "Check your email",
        "We sent you a confirmation link. Please verify before signing in.",
      );
    }
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <KeyboardAvoidingView
        className="flex-1 justify-center px-6"
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <View className="mb-10 items-center">
          <Text className="text-brand-400 text-4xl font-bold tracking-tight">AutoFounder</Text>
          <Text className="text-slate-400 text-base mt-2">Create your account</Text>
        </View>

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

        <Text className="text-slate-400 text-sm font-medium mb-1">Password</Text>
        <TextInput
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-xl px-4 py-3.5 text-base mb-4"
          placeholder="At least 8 characters"
          placeholderTextColor="#64748b"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <Text className="text-slate-400 text-sm font-medium mb-1">Confirm password</Text>
        <TextInput
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-xl px-4 py-3.5 text-base mb-6"
          placeholder="••••••••"
          placeholderTextColor="#64748b"
          secureTextEntry
          value={confirmPassword}
          onChangeText={setConfirmPassword}
        />

        <TouchableOpacity
          className="bg-brand-500 rounded-xl py-4 items-center mb-4"
          onPress={handleSignUp}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white font-semibold text-base">Create account</Text>
          )}
        </TouchableOpacity>

        <View className="flex-row justify-center">
          <Text className="text-slate-400 text-sm">Already have an account? </Text>
          <Link href="/(auth)/login" asChild>
            <TouchableOpacity>
              <Text className="text-brand-400 text-sm font-semibold">Sign in</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
