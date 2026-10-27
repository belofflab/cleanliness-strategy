// Профиль: данные пользователя, базовый URL API и выход.
import { router } from "expo-router";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { api } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { theme } from "@/theme";

export default function ProfileScreen() {
  const { user, signOut } = useAuth();

  async function onSignOut() {
    await signOut();
    router.replace("/(auth)/login");
  }

  return (
    <View style={styles.screen}>
      <View style={styles.card}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {(user?.full_name || user?.phone || "?").slice(0, 1).toUpperCase()}
          </Text>
        </View>
        <Text style={styles.name}>{user?.full_name || "Клиент"}</Text>
        <Text style={styles.muted}>{user?.phone}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{user?.role}</Text>
        </View>
      </View>

      <View style={styles.infoRow}>
        <Text style={styles.muted}>API</Text>
        <Text style={styles.infoValue} numberOfLines={1}>
          {api.base}
        </Text>
      </View>

      <Pressable
        style={styles.logout}
        onPress={() =>
          Alert.alert("Выход", "Выйти из аккаунта?", [
            { text: "Отмена", style: "cancel" },
            { text: "Выйти", style: "destructive", onPress: onSignOut },
          ])
        }
      >
        <Text style={styles.logoutText}>Выйти</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.bg, padding: 16 },
  card: {
    backgroundColor: theme.colors.card,
    borderRadius: theme.radius,
    borderWidth: 1,
    borderColor: theme.colors.border,
    alignItems: "center",
    padding: 24,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: theme.colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  avatarText: { color: "#fff", fontSize: 28, fontWeight: "800" },
  name: { fontSize: 20, fontWeight: "700", color: theme.colors.text },
  muted: { color: theme.colors.muted, fontSize: 14 },
  badge: {
    marginTop: 10,
    backgroundColor: theme.colors.bg,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  badgeText: { color: theme.colors.primary, fontWeight: "600", fontSize: 12 },
  infoRow: {
    marginTop: 16,
    backgroundColor: theme.colors.card,
    borderRadius: theme.radius,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: 16,
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 16,
  },
  infoValue: { color: theme.colors.text, flexShrink: 1, fontWeight: "600" },
  logout: {
    marginTop: "auto",
    borderWidth: 1,
    borderColor: theme.colors.danger,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  logoutText: { color: theme.colors.danger, fontSize: 16, fontWeight: "700" },
});

