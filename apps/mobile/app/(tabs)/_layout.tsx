import { Redirect, Tabs } from "expo-router";

import { useAuth } from "@/auth/AuthContext";
import { theme } from "@/theme";

export default function TabsLayout() {
  const { user, isLoading } = useAuth();

  // Гард: без авторизации — назад на логин.
  if (!isLoading && !user) return <Redirect href="/(auth)/login" />;

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.muted,
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Заказать", headerTitle: "Новая заявка" }} />
      <Tabs.Screen name="profile" options={{ title: "Профиль", headerTitle: "Профиль" }} />
    </Tabs>
  );
}

