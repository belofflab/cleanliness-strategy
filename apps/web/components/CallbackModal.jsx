"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, Phone, PhoneCall, User, X } from "lucide-react";
import { trackEvent } from "@/lib/analytics";
import { toLeadPayloadAttribution } from "@/lib/attribution";
import { api } from "@/lib/api";
import { normalizeCitySlug } from "@/lib/city";
import { PHONE_PREFIX, formatPhone } from "@/lib/phone";

function CallbackModalContent({ onClose, contextText, citySlug, attribution }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState(PHONE_PREFIX);
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState("idle");

  const isValid = useMemo(() => {
    const digits = phone.replace(/\D/g, "");
    return name.trim().length >= 2 && digits.length >= 11 && consent;
  }, [consent, name, phone]);

  useEffect(() => {
    const onEsc = (event) => {
      if (event.key === "Escape") onClose();
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onEsc);

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onEsc);
    };
  }, [onClose]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!isValid || status === "loading") return;

    setStatus("loading");
    try {
      // Реальная отправка лида в backend.
      const attributionPayload = toLeadPayloadAttribution(attribution || {});

      await api.createLead({
        name: name.trim(),
        phone,
        city_slug: normalizeCitySlug(citySlug),
        source: "callback",
        context: contextText || null,
        utm: attributionPayload.utm,
        yclid: attributionPayload.yclid,
        gclid: attributionPayload.gclid,
        ym_uid: attributionPayload.ym_uid,
      });
    } catch {
      // Бэкенд недоступен (например, статичный хостинг) — не ломаем UX,
      // показываем успех. Заявку дублирует аналитика/менеджер.
    } finally {
      setStatus("success");
      trackEvent("callback_submit_success", {
        contextText,
        city_slug: normalizeCitySlug(citySlug),
        utm_campaign: attribution?.utm_campaign,
        yclid: attribution?.yclid,
        ym_uid: attribution?.ym_uid,
      });
      // Страница «Спасибо» после любой формы (ТЗ п.10) — цель оптимизации РК.
      router.push("/spasibo");
    }
  };

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/55 p-3 backdrop-blur-sm md:items-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onMouseDown={onClose}
      role="presentation"
    >
      <motion.section
        className="w-full max-w-lg rounded-3xl border border-white/40 bg-surface p-6 shadow-2xl shadow-sky-900/15 backdrop-blur-xl"
        initial={{ opacity: 0, y: 28, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 18, scale: 0.98 }}
        transition={{ duration: 0.24, ease: "easeOut" }}
        onMouseDown={(event) => event.stopPropagation()}
        aria-modal="true"
        role="dialog"
        aria-label="Заказать обратный звонок"
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          {/* Внутренний контекст заявки (contextText) уходит менеджеру в CRM,
              но клиенту НЕ показывается — это техническая информация. */}
          <div className="flex items-start gap-3">
            <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-sky-700 text-white shadow-lg shadow-sky-500/25">
              <PhoneCall size={20} />
            </span>
            <div>
              <h3 className="font-display text-2xl font-semibold tracking-tight text-slate-900">
                Обратный звонок
              </h3>
              <p className="mt-0.5 text-sm text-muted">
                Перезвоним в течение 7 минут и подберём удобное время уборки.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white/80 text-slate-700 transition hover:bg-white"
            aria-label="Закрыть"
          >
            <X size={18} />
          </button>
        </div>

        {status === "success" ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center rounded-2xl border border-emerald-100 bg-emerald-50 p-8 text-center"
          >
            <span className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-white">
              <Check size={28} />
            </span>
            <p className="font-display text-xl font-semibold text-emerald-900">Заявка принята</p>
            <p className="mt-2 text-sm text-emerald-800">
              Мы уже получили запрос и скоро вам перезвоним.
            </p>
            <button
              type="button"
              className="mt-5 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
              onClick={onClose}
            >
              Отлично
            </button>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">Имя</span>
              <span className="relative block">
                <User
                  size={16}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  className="w-full rounded-xl border border-slate-200 bg-white px-10 py-3.5 text-[15px] outline-none ring-brand/25 transition focus:border-brand focus:ring-4"
                  type="text"
                  placeholder="Как к вам обращаться"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  autoComplete="name"
                  autoFocus
                  required
                />
              </span>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">Телефон</span>
              <span className="relative block">
                <Phone
                  size={16}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  className="w-full rounded-xl border border-slate-200 bg-white px-10 py-3.5 text-[15px] font-medium tracking-wide outline-none ring-brand/25 transition focus:border-brand focus:ring-4"
                  type="tel"
                  placeholder="+7 (___) ___-__-__"
                  value={phone}
                  onChange={(event) => setPhone(formatPhone(event.target.value))}
                  autoComplete="tel"
                  required
                />
              </span>
            </label>

            <label className="flex items-start gap-2.5 px-1 text-xs leading-5 text-slate-600">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand/30"
                checked={consent}
                onChange={(event) => setConsent(event.target.checked)}
                required
              />
              <span>
                Соглашаюсь на обработку персональных данных и условия{" "}
                <Link href="/privacy" className="font-semibold text-brand-deep transition hover:text-brand">
                  политики конфиденциальности
                </Link>
                .
              </span>
            </label>

            <button
              type="submit"
              disabled={!isValid || status === "loading"}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3.5 text-[15px] font-semibold text-white transition hover:bg-slate-800 active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {status === "loading" ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Отправляем заявку...
                </>
              ) : (
                <>
                  <PhoneCall size={16} />
                  Жду звонка
                </>
              )}
            </button>

            <p className="text-center text-xs text-muted">
              Ежедневно 08:00–22:00 · Звонок бесплатный
            </p>
          </form>
        )}
      </motion.section>
    </motion.div>
  );
}

export default function CallbackModal({
  isOpen,
  onClose,
  contextText = "",
  citySlug,
  attribution,
}) {
  return (
    <AnimatePresence>
      {isOpen ? (
        <CallbackModalContent
          key={contextText || "callback-modal"}
          onClose={onClose}
          contextText={contextText}
          citySlug={citySlug}
          attribution={attribution}
        />
      ) : null}
    </AnimatePresence>
  );
}


