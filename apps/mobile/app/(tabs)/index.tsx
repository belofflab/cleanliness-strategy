// Главный экран: оформление заявки (расчёт + выбор слота + бронирование).
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api, DEFAULT_CITY } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import type { QuoteResponse, Slot } from "@/api/types";
import { theme } from "@/theme";

const SERVICES = [
  { code: "maintenance", label: "Поддерживающая" },
  { code: "general", label: "Генеральная" },
  { code: "post_renovation", label: "После ремонта" },
];

function Stepper({ value, onChange, label }: { value: number; onChange: (n: number) => void; label: string }) {
  return (
    <View style={styles.stepperRow}>
      <Text style={styles.stepperLabel}>{label}</Text>
      <View style={styles.stepper}>
        <Pressable style={styles.stepBtn} onPress={() => onChange(Math.max(0, value - 1))}>
          <Text style={styles.stepBtnText}>−</Text>
        </Pressable>
        <Text style={styles.stepValue}>{value}</Text>
        <Pressable style={styles.stepBtn} onPress={() => onChange(value + 1)}>
          <Text style={styles.stepBtnText}>+</Text>
        </Pressable>
      </View>
    </View>
  );
}

export default function BookingScreen() {
  const { user } = useAuth();
  const [name, setName] = useState(user?.full_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [serviceType, setServiceType] = useState("general");
  const [rooms, setRooms] = useState(2);
  const [bathrooms, setBathrooms] = useState(1);

  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [slotId, setSlotId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Динамический расчёт стоимости при изменении параметров.
  useEffect(() => {
    const controller = new AbortController();
    const t = setTimeout(async () => {
      try {
        const q = await api.getQuote({
          city_slug: DEFAULT_CITY,
          service_type: serviceType,
          rooms,
          bathrooms,
          addon_codes: [],
        });
        if (!controller.signal.aborted) setQuote(q);
      } catch {
        if (!controller.signal.aborted) setQuote(null);
      }
    }, 250);
    return () => {
      controller.abort();
      clearTimeout(t);
    };
  }, [serviceType, rooms, bathrooms]);

  // Свободные слоты мастеров.
  useEffect(() => {
    api
      .getAvailability(DEFAULT_CITY)
      .then(setSlots)
      .catch(() => setSlots([]));
  }, []);

  const totalLabel = useMemo(
    () => (quote ? `${quote.total.toLocaleString("ru-RU")} ${quote.currency}` : "—"),
    [quote]
  );

  async function onSubmit() {
    if (name.trim().length < 1 || phone.trim().length < 5) {
      Alert.alert("Заполните контакты", "Укажите имя и телефон.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.createBooking({
        name: name.trim(),
        phone: phone.trim(),
        city_slug: DEFAULT_CITY,
        service_type: serviceType,
        rooms,
        bathrooms,
        addon_codes: [],
        schedule_id: slotId,
        source: "mobile",
      });
      Alert.alert(
        "Заявка принята 🎉",
        `${res.message}\n\nИтого: ${res.total.toLocaleString("ru-RU")} ₽\nВремя работ: ${res.est_time_human}` +
          (res.master_name ? `\nМастер: ${res.master_name}` : ""),
      );
      setSlotId(null);
    } catch (e) {
      Alert.alert("Не удалось оформить", e instanceof Error ? e.message : "Попробуйте позже");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Text style={styles.section}>Контакты</Text>
      <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Ваше имя" placeholderTextColor={theme.colors.muted} />
      <TextInput
        style={styles.input}
        value={phone}
        onChangeText={setPhone}
        placeholder="+7 ..."
        keyboardType="phone-pad"
        placeholderTextColor={theme.colors.muted}
      />

      <Text style={styles.section}>Тип уборки</Text>
      <View style={styles.chips}>
        {SERVICES.map((s) => (
          <Pressable
            key={s.code}
            style={[styles.chip, serviceType === s.code && styles.chipActive]}
            onPress={() => setServiceType(s.code)}
          >
            <Text style={[styles.chipText, serviceType === s.code && styles.chipTextActive]}>{s.label}</Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.section}>Параметры</Text>
      <View style={styles.card}>
        <Stepper label="Комнаты" value={rooms} onChange={setRooms} />
        <View style={styles.divider} />
        <Stepper label="Санузлы" value={bathrooms} onChange={setBathrooms} />
      </View>

      <Text style={styles.section}>Удобное время</Text>
      {slots.length === 0 ? (
        <Text style={styles.muted}>Свободных слотов нет — подберём по телефону.</Text>
      ) : (
        <View style={styles.chips}>
          {slots.slice(0, 8).map((s) => {
            const active = slotId === s.id;
            return (
              <Pressable
                key={s.id}
                style={[styles.slot, active && styles.chipActive]}
                onPress={() => setSlotId(active ? null : s.id)}
              >
                <Text style={[styles.chipText, active && styles.chipTextActive]}>
                  {s.work_date} · {s.start_time.slice(0, 5)}
                </Text>
                <Text style={[styles.slotMaster, active && styles.chipTextActive]}>{s.master_name}</Text>
              </Pressable>
            );
          })}
        </View>
      )}

      <View style={styles.summary}>
        <View>
          <Text style={styles.muted}>Итого</Text>
          <Text style={styles.total}>{totalLabel}</Text>
          {quote ? <Text style={styles.muted}>≈ {quote.est_time_human}</Text> : null}
        </View>
        <Pressable style={[styles.cta, submitting && styles.buttonDisabled]} onPress={onSubmit} disabled={submitting}>
          {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.ctaText}>Оформить</Text>}
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.bg },
  content: { padding: 16, paddingBottom: 48 },
  section: { fontSize: 16, fontWeight: "700", color: theme.colors.text, marginTop: 18, marginBottom: 10 },
  input: {
    backgroundColor: theme.colors.card,
    borderWidth: 1,
    borderColor: theme.colors.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    color: theme.colors.text,
    marginBottom: 10,
  },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.card,
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  chipActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
  chipText: { color: theme.colors.text, fontWeight: "600" },
  chipTextActive: { color: "#fff" },
  card: {
    backgroundColor: theme.colors.card,
    borderRadius: theme.radius,
    borderWidth: 1,
    borderColor: theme.colors.border,
    paddingHorizontal: 16,
  },
  divider: { height: 1, backgroundColor: theme.colors.border },
  stepperRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: 14 },
  stepperLabel: { fontSize: 16, color: theme.colors.text },
  stepper: { flexDirection: "row", alignItems: "center", gap: 16 },
  stepBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: theme.colors.bg,
    borderWidth: 1,
    borderColor: theme.colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  stepBtnText: { fontSize: 22, color: theme.colors.primary, fontWeight: "700", lineHeight: 24 },
  stepValue: { fontSize: 18, fontWeight: "700", color: theme.colors.text, minWidth: 24, textAlign: "center" },
  slot: {
    borderWidth: 1,
    borderColor: theme.colors.border,
    backgroundColor: theme.colors.card,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  slotMaster: { fontSize: 12, color: theme.colors.muted, marginTop: 2 },
  muted: { color: theme.colors.muted, fontSize: 14 },
  summary: {
    marginTop: 24,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: theme.colors.card,
    borderRadius: theme.radius,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: 16,
  },
  total: { fontSize: 24, fontWeight: "800", color: theme.colors.text },
  cta: {
    backgroundColor: theme.colors.primary,
    borderRadius: 12,
    paddingHorizontal: 28,
    paddingVertical: 14,
  },
  ctaText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  buttonDisabled: { opacity: 0.6 },
});

