import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AuthProvider } from "@/auth/AuthContext";

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar style="dark" />
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="(auth)/login" />
          <Stack.Screen name="(tabs)" />
        </Stack>
      </AuthProvider>
    </SafeAreaProvider>
  );
}

