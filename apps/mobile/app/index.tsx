// Точка входа: ждём восстановления сессии и редиректим.
import { Redirect } from "expo-router";
import { ActivityIndicator, View } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { theme } from "@/theme";

export default function Index() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", backgroundColor: theme.colors.bg }}>
        <ActivityIndicator color={theme.colors.primary} size="large" />
      </View>
    );
  }

  return <Redirect href={user ? "/(tabs)" : "/(auth)/login"} />;
}

