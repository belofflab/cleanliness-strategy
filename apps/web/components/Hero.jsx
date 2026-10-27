"use client";

import { useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowRight, Clock3, MessageCircleMore, PhoneCall, Send, ShieldCheck, Timer } from "lucide-react";
import { trackCallGoal, trackEvent } from "@/lib/analytics";

function toPhoneHref(phone) {
  return `tel:${phone.replace(/[^\d+]/g, "")}`;
}

// Микропреимущества под заголовком (ТЗ п.7).
const MICRO_BENEFITS = [
  { icon: Timer, text: "Ответим до 7 минут" },
  { icon: Clock3, text: "Работаем ежедневно 08:00–22:00" },
  { icon: ShieldCheck, text: "Цена согласуется до начала работ" },
];

export default function Hero({
  onOpenCallback,
  cityName = "Уфа",
  cityNamePrepositional = "в Уфе",
  cityPhone = "+7 (993) 138-50-53",
  headline,
}) {
  // Фото реальной команды: положите файл в apps/web/public/hero-team.jpg —
  // блок появится автоматически (до этого показываем только карточку связи).
  const [teamPhotoAvailable, setTeamPhotoAvailable] = useState(true);
  const resolvedHeadline =
    headline || `Профессиональная уборка квартир и офисов ${cityNamePrepositional}`;

  return (
    <section id="hero" className="relative overflow-hidden px-4 pb-16 pt-6 sm:px-6 lg:px-10">
      <div className="pointer-events-none absolute -left-20 top-0 h-64 w-64 rounded-full bg-sky-300/40 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 top-16 h-64 w-64 rounded-full bg-cyan-200/50 blur-3xl" />

      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
        <div className="grid gap-8 lg:grid-cols-[1.25fr_1fr] lg:items-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
          >
            <p className="mb-4 inline-flex rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-brand-deep">
              Точка Чистоты • {cityName}
            </p>
            <h1 className="font-display text-4xl font-semibold leading-tight tracking-tight text-slate-950 sm:text-5xl">
              {resolvedHeadline}
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
              Поддерживающая, генеральная уборка и клининг после ремонта. Привезём средства
              и инвентарь, согласуем стоимость до выезда — оплата после приёмки.
            </p>

            <ul className="mt-5 flex flex-wrap gap-2">
              {MICRO_BENEFITS.map((benefit) => {
                const Icon = benefit.icon;
                return (
                  <li
                    key={benefit.text}
                    className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700"
                  >
                    <Icon size={13} className="text-brand-deep" />
                    {benefit.text}
                  </li>
                );
              })}
            </ul>

            <div className="mt-6 grid gap-3 sm:max-w-md sm:grid-cols-2">
              <a
                href="#calculator"
                onClick={() => trackEvent("cta_click", { place: "hero", target: "calculator" })}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Рассчитать стоимость
                <ArrowRight size={16} />
              </a>
              <button
                type="button"
                onClick={() => onOpenCallback("Заказ уборки с Hero-блока")}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3.5 text-sm font-semibold text-slate-800 transition hover:border-slate-300 hover:bg-slate-50"
              >
                Заказать уборку
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.45 }}
            className="space-y-3"
          >
            {teamPhotoAvailable ? (
              <div className="relative h-52 overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 sm:h-64">
                <Image
                  src="/hero-team.jpg"
                  alt={`Команда «Точка Чистоты» на объекте ${cityNamePrepositional}`}
                  fill
                  sizes="(max-width: 1024px) 100vw, 420px"
                  className="object-cover"
                  onError={() => setTeamPhotoAvailable(false)}
                  priority
                />
              </div>
            ) : null}

            <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Быстрая связь</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <a
                  href="https://t.me/pointclean"
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => trackEvent("messenger_click", { messenger: "telegram", place: "hero" })}
                  className="inline-flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-600"
                >
                  <Send size={15} />
                  Telegram
                </a>
                <a
                  href="https://max.ru/u/f9LHodD0cOJ-1c8HG-4TAxVQZJip_UiDUg0UWG0JD0mSYbnaQFc9UpKhxs0"
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => trackEvent("messenger_click", { messenger: "max", place: "hero" })}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-600"
                >
                  <MessageCircleMore size={15} />
                  Max
                </a>
                <button
                  type="button"
                  onClick={() => onOpenCallback("Запрос звонка с Hero-блока")}
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  <PhoneCall size={15} />
                  Обратный звонок
                </button>
              </div>
              <div className="mt-3 space-y-1 text-sm font-medium text-slate-700">
                <a
                  className="block transition hover:text-brand-deep"
                  href={toPhoneHref(cityPhone)}
                  onClick={() => {
                    const payload = { place: "hero", phone: cityPhone, city: cityName };
                    trackEvent("phone_click", payload);
                    trackCallGoal(payload);
                  }}
                >
                  {cityPhone}
                </a>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
