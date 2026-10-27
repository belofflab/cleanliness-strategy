// Экран входа по OTP (телефон -> код -> токены).
import { router } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { ApiError } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { theme } from "@/theme";

export default function LoginScreen() {
  const { requestCode, verifyCode } = useAuth();
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);

  async function onRequest() {
    if (phone.trim().length < 5) {
      Alert.alert("Проверьте номер", "Введите телефон в формате +7 ...");
      return;
    }
    setBusy(true);
    try {
      const { debugCode } = await requestCode(phone.trim());
      setStep("code");
      if (debugCode) {
        // dev/mock-режим backend возвращает код — подставим для удобства тестирования.
        setCode(debugCode);
        Alert.alert("Код отправлен", `DEV-код: ${debugCode}`);
      }
    } catch (e) {
      Alert.alert("Ошибка", e instanceof ApiError ? e.message : "Не удалось отправить код");
    } finally {
      setBusy(false);
    }
  }

  async function onVerify() {
    setBusy(true);
    try {
      await verifyCode(phone.trim(), code.trim());
      router.replace("/(tabs)");
    } catch (e) {
      Alert.alert("Ошибка", e instanceof ApiError ? e.message : "Неверный код");
    } finally {
      setBusy(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.container}
      >
        <View style={styles.brand}>
          <Text style={styles.logo}>Точка Чистоты</Text>
          <Text style={styles.subtitle}>Вход в личный кабинет</Text>
        </View>

        {step === "phone" ? (
          <View style={styles.card}>
            <Text style={styles.label}>Номер телефона</Text>
            <TextInput
              value={phone}
              onChangeText={setPhone}
              placeholder="+7 (917) 000-00-00"
              keyboardType="phone-pad"
              autoFocus
              style={styles.input}
              placeholderTextColor={theme.colors.muted}
            />
            <Pressable
              style={[styles.button, busy && styles.buttonDisabled]}
              onPress={onRequest}
              disabled={busy}
            >
              {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Получить код</Text>}
            </Pressable>
          </View>
        ) : (
          <View style={styles.card}>
            <Text style={styles.label}>Код из SMS</Text>
            <TextInput
              value={code}
              onChangeText={setCode}
              placeholder="1234"
              keyboardType="number-pad"
              maxLength={6}
              autoFocus
              style={styles.input}
              placeholderTextColor={theme.colors.muted}
            />
            <Pressable
              style={[styles.button, busy && styles.buttonDisabled]}
              onPress={onVerify}
              disabled={busy}
            >
              {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Войти</Text>}
            </Pressable>
            <Pressable onPress={() => setStep("phone")} style={styles.linkWrap}>
              <Text style={styles.link}>Изменить номер</Text>
            </Pressable>
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  brand: { alignItems: "center", marginBottom: 32 },
  logo: { fontSize: 28, fontWeight: "800", color: theme.colors.primary },
  subtitle: { fontSize: 15, color: theme.colors.muted, marginTop: 6 },
  card: {
    backgroundColor: theme.colors.card,
    borderRadius: theme.radius,
    padding: 20,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  label: { fontSize: 14, fontWeight: "600", color: theme.colors.text, marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 18,
    color: theme.colors.text,
    marginBottom: 16,
  },
  button: {
    backgroundColor: theme.colors.primary,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  linkWrap: { marginTop: 14, alignItems: "center" },
  link: { color: theme.colors.primary, fontSize: 14, fontWeight: "600" },
});

