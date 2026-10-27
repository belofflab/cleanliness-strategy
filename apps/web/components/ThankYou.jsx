"use client";

import { useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Check, MessageCircleMore, PhoneCall, Send, Timer } from "lucide-react";
import { trackEvent } from "@/lib/analytics";
import { getCityProfile, readCitySlugCookie } from "@/lib/city";
import Logo from "@/components/Logo";

export default function ThankYou() {
  useEffect(() => {
    // Цель для оптимизации рекламных кампаний (ТЗ п.10): визит страницы «Спасибо».
    trackEvent("thankyou_view", { page: "/spasibo" });
  }, []);

  const city = getCityProfile(typeof document === "undefined" ? null : readCitySlugCookie());

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-16 sm:px-6">
      <div className="pointer-events-none absolute -left-20 top-0 h-64 w-64 rounded-full bg-sky-300/40 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 bottom-16 h-64 w-64 rounded-full bg-cyan-200/50 blur-3xl" />

      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-xl rounded-[2rem] border border-white/40 bg-surface p-8 text-center shadow-xl shadow-slate-900/5 backdrop-blur-xl sm:p-10"
      >
        <div className="flex justify-center">
          <Logo size={36} textClassName="text-xl text-slate-950" />
        </div>

        <span className="mt-8 inline-flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/30">
          <Check size={32} />
        </span>

        <h1 className="mt-5 font-display text-3xl font-semibold tracking-tight text-slate-950">
          Спасибо! Заявка принята
        </h1>
        <p className="mx-auto mt-3 max-w-md text-base leading-relaxed text-muted">
          Менеджер уже видит ваш запрос и полный расчёт.
        </p>
        <p className="mt-4 inline-flex items-center gap-2 rounded-full bg-sky-50 px-4 py-2 text-sm font-semibold text-sky-900">
          <Timer size={15} />
          Ответим в течение 7 минут (ежедневно 08:00–22:00)
        </p>

        <div className="mt-7 grid gap-2 sm:grid-cols-3">
          <a
            href="https://t.me/pointclean"
            target="_blank"
            rel="noreferrer"
            onClick={() => trackEvent("messenger_click", { messenger: "telegram", place: "thankyou" })}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-sky-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-600"
          >
            <Send size={15} /> Telegram
          </a>
          <a
            href="https://max.ru/u/f9LHodD0cOJ-1c8HG-4TAxVQZJip_UiDUg0UWG0JD0mSYbnaQFc9UpKhxs0"
            target="_blank"
            rel="noreferrer"
            onClick={() => trackEvent("messenger_click", { messenger: "max", place: "thankyou" })}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-600"
          >
            <MessageCircleMore size={15} /> Max
          </a>
          <a
            href={`tel:${city.phone.replace(/[^\d+]/g, "")}`}
            onClick={() => trackEvent("phone_click", { place: "thankyou", phone: city.phone })}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
          >
            <PhoneCall size={15} /> Позвонить
          </a>
        </div>

        <Link
          href="/"
          className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-brand-deep"
        >
          <ArrowLeft size={15} />
          Вернуться на главную
        </Link>
      </motion.section>
    </main>
  );
}
