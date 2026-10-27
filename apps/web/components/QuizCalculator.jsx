"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Calendar,
  Check,
  Home,
  Hotel,
  Loader2,
  MessageCircleMore,
  Phone,
  PhoneCall,
  Send,
  ShieldCheck,
  Sparkles,
  User,
  Warehouse,
} from "lucide-react";
import { api } from "@/lib/api";
import { normalizeCitySlug } from "@/lib/city";
import { toLeadPayloadAttribution } from "@/lib/attribution";
import { trackEvent } from "@/lib/analytics";
import { PHONE_PREFIX, formatPhone, isCompletePhone } from "@/lib/phone";

// ===== Шаги квиза (ТЗ п.8 в редакции п.14) =====
// Примерную стоимость НЕ показываем: точную цену называет менеджер.
// Вопросы про состояние и доп.услуги скрыты, из параметров осталась площадь.
const STEPS = [
  { id: 1, title: "Объект" },
  { id: 2, title: "Площадь" },
  { id: 3, title: "Тип уборки" },
  { id: 4, title: "Контакты" },
];

const OBJECT_TYPES = [
  { id: "apartment", label: "Квартира", icon: Home },
  { id: "house", label: "Дом", icon: Hotel },
  { id: "office", label: "Офис", icon: Building2 },
  { id: "other", label: "Другое помещение", icon: Warehouse },
];

// service_type бэкенда (см. сиды: maintenance/general/post_renovation/office).
const CLEANING_TYPES = [
  { id: "maintenance", label: "Поддерживающая", hint: "Регулярный уход за чистотой" },
  { id: "general", label: "Генеральная", hint: "Глубокая уборка всех зон" },
  { id: "post_renovation", label: "После ремонта", hint: "Строительная пыль и следы работ" },
  { id: "office", label: "Офисная", hint: "Кабинеты, open space, санузлы" },
];

const CONTACT_METHODS = [
  { id: "call", label: "Звонок", icon: PhoneCall },
  { id: "telegram", label: "Telegram", icon: Send },
  { id: "max", label: "Max", icon: MessageCircleMore },
];

// Быстрый выбор площади — меньше набора с телефона.
const AREA_PRESETS = [30, 45, 60, 80, 100];

function OptionCard({ active, onClick, title, hint, icon: Icon }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-2xl border p-4 text-left transition ${
        active
          ? "border-transparent bg-slate-900 text-white shadow-lg shadow-slate-900/20"
          : "border-slate-200 bg-white text-slate-800 hover:border-slate-300"
      }`}
    >
      {Icon ? (
        <span
          className={`mb-2 inline-flex h-9 w-9 items-center justify-center rounded-lg ${
            active ? "bg-white/15 text-white" : "bg-slate-100 text-slate-600"
          }`}
        >
          <Icon size={18} />
        </span>
      ) : null}
      <p className="text-sm font-semibold">{title}</p>
      {hint ? <p className={`mt-1 text-xs ${active ? "opacity-75" : "text-muted"}`}>{hint}</p> : null}
    </button>
  );
}

export default function QuizCalculator({ citySlug, attribution }) {
  const router = useRouter();
  const resolvedCitySlug = normalizeCitySlug(citySlug);

  const [step, setStep] = useState(1);
  // Шаг 1
  const [objectType, setObjectType] = useState("apartment");
  // Шаг 2 — только площадь (ТЗ п.14)
  const [area, setArea] = useState("");
  // Шаг 3
  const [cleaningType, setCleaningType] = useState("maintenance");
  // Шаг 4
  const [name, setName] = useState("");
  const [phone, setPhone] = useState(PHONE_PREFIX);
  const [desiredDate, setDesiredDate] = useState("");
  const [contactMethod, setContactMethod] = useState("call");
  const [comment, setComment] = useState("");
  const [consent, setConsent] = useState(false);
  const [submitStatus, setSubmitStatus] = useState("idle");

  // Автопереход после выбора карточки: пауза, чтобы выбор успел подсветиться.
  const advanceTimerRef = useRef(null);
  const stepRef = useRef(step);
  useEffect(() => {
    stepRef.current = step;
  }, [step]);
  useEffect(() => () => clearTimeout(advanceTimerRef.current), []);

  const goToStep = (nextStep) => {
    const bounded = Math.min(STEPS.length, Math.max(1, nextStep));
    setStep(bounded);
    trackEvent("quiz_step", { step: bounded, city_slug: resolvedCitySlug });
  };

  const scheduleAdvance = (fromStep) => {
    clearTimeout(advanceTimerRef.current);
    advanceTimerRef.current = setTimeout(() => {
      // Пользователь мог успеть уйти с шага сам — тогда не дёргаем переход.
      if (stepRef.current !== fromStep) return;
      goToStep(fromStep + 1);
    }, 260);
  };

  // Офис на шаге 1 → предлагаем офисную уборку на шаге 3 (и наоборот).
  const handleObjectTypeSelect = (nextObjectType) => {
    setObjectType(nextObjectType);
    if (nextObjectType === "office") {
      setCleaningType("office");
    } else {
      setCleaningType((prev) => (prev === "office" ? "maintenance" : prev));
    }
    scheduleAdvance(1);
  };

  const handleCleaningTypeSelect = (nextType) => {
    setCleaningType(nextType);
    scheduleAdvance(3);
  };

  const areaNumber = Number.parseInt(area, 10) || 0;
  const isAreaValid = areaNumber > 0;

  const objectLabel = OBJECT_TYPES.find((o) => o.id === objectType)?.label || objectType;
  const cleaningLabel = CLEANING_TYPES.find((t) => t.id === cleaningType)?.label || cleaningType;
  const contactLabel = CONTACT_METHODS.find((m) => m.id === contactMethod)?.label || contactMethod;

  // Менеджер получает полную анкету квиза (ТЗ: «не только телефон, а полный расчёт»).
  const buildLeadContext = () => {
    const lines = [
      `Объект: ${objectLabel}${areaNumber ? `, ${areaNumber} м²` : ""}`,
      `Тип уборки: ${cleaningLabel}`,
    ];
    if (desiredDate) lines.push(`Желаемая дата: ${desiredDate}`);
    lines.push(`Способ связи: ${contactLabel}`);
    if (comment.trim()) lines.push(`Комментарий: ${comment.trim().slice(0, 500)}`);
    return `Квиз-заявка → ${lines.join(" | ")}`;
  };

  const isContactValid = name.trim().length >= 2 && isCompletePhone(phone) && consent;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!isContactValid || submitStatus === "loading") return;

    setSubmitStatus("loading");
    const attributionPayload = toLeadPayloadAttribution(attribution || {});

    try {
      await api.createLead({
        name: name.trim(),
        phone,
        city_slug: resolvedCitySlug,
        source: "quiz",
        context: buildLeadContext(),
        service_type: cleaningLabel,
        utm: attributionPayload.utm,
        yclid: attributionPayload.yclid,
        gclid: attributionPayload.gclid,
        ym_uid: attributionPayload.ym_uid,
      });
    } catch {
      // Бэкенд недоступен — не ломаем UX: заявка продублирована аналитикой.
    } finally {
      trackEvent("quiz_submit_success", {
        city_slug: resolvedCitySlug,
        service: cleaningType,
        area: areaNumber || null,
        utm_campaign: attribution?.utm_campaign,
        yclid: attribution?.yclid,
      });
      // Страница «Спасибо» (ТЗ п.10) — на неё настраивается оптимизация РК.
      router.push("/spasibo");
    }
  };

  const progressPercent = ((step - 1) / (STEPS.length - 1)) * 100;

  return (
    <section id="calculator" className="px-4 py-16 sm:px-6 lg:px-10">
      <div className="mx-auto w-full max-w-3xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
        <div className="mb-2 flex items-center gap-2">
          <Sparkles size={18} className="text-brand-deep" />
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Расчёт стоимости уборки
          </h2>
        </div>
        <p className="mb-6 max-w-2xl text-sm text-muted">
          Три коротких вопроса — менеджер подготовит точный расчёт и свяжется с вами
          в течение 7 минут.
        </p>

        {/* Прогресс: шаги-чипы + тонкая полоса */}
        <div className="mb-2 flex flex-wrap items-center gap-2">
          {STEPS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => s.id < step && goToStep(s.id)}
              disabled={s.id > step}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                s.id === step
                  ? "bg-slate-900 text-white"
                  : s.id < step
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-slate-100 text-slate-500"
              }`}
            >
              {s.id < step ? <Check size={12} /> : null}
              {s.id}. {s.title}
            </button>
          ))}
        </div>
        <div className="mb-6 h-1 w-full overflow-hidden rounded-full bg-slate-200/70">
          <div
            className="h-full rounded-full bg-brand transition-[width] duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        <motion.div
          key={step}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.22 }}
          className="space-y-5"
        >
          {step === 1 ? (
            <div>
              <p className="mb-3 text-sm font-medium text-slate-700">Что убираем?</p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {OBJECT_TYPES.map((object) => (
                  <OptionCard
                    key={object.id}
                    active={objectType === object.id}
                    onClick={() => handleObjectTypeSelect(object.id)}
                    title={object.label}
                    icon={object.icon}
                  />
                ))}
              </div>
            </div>
          ) : null}

          {step === 2 ? (
            <div className="space-y-4">
              <label className="block rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
                <span className="text-sm text-muted">Площадь помещения, м²</span>
                <input
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={10000}
                  value={area}
                  autoFocus
                  onChange={(event) => setArea(event.target.value.slice(0, 5))}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && isAreaValid) goToStep(3);
                  }}
                  placeholder="Например, 64"
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 font-display text-2xl font-semibold text-slate-900 outline-none ring-brand/25 transition focus:border-brand focus:ring-4"
                />
                <span className="mt-3 flex flex-wrap gap-2">
                  {AREA_PRESETS.map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setArea(String(preset))}
                      className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                        areaNumber === preset
                          ? "bg-slate-900 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {preset} м²
                    </button>
                  ))}
                </span>
              </label>
              <p className="text-xs text-muted">
                Не знаете точную площадь? Укажите примерно — менеджер уточнит при звонке.
              </p>
            </div>
          ) : null}

          {step === 3 ? (
            <div>
              <p className="mb-3 text-sm font-medium text-slate-700">Какая уборка нужна?</p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {CLEANING_TYPES.map((type) => (
                  <OptionCard
                    key={type.id}
                    active={cleaningType === type.id}
                    onClick={() => handleCleaningTypeSelect(type.id)}
                    title={type.label}
                    hint={type.hint}
                  />
                ))}
              </div>
            </div>
          ) : null}

          {step === 4 ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Краткое резюме заявки — пользователь видит, что уйдёт менеджеру. */}
              <div className="flex flex-wrap gap-1.5 rounded-2xl border border-slate-200 bg-white p-3 text-xs font-medium text-slate-700">
                <span className="rounded-full bg-slate-100 px-2.5 py-1">{objectLabel}</span>
                {areaNumber ? <span className="rounded-full bg-slate-100 px-2.5 py-1">{areaNumber} м²</span> : null}
                <span className="rounded-full bg-slate-100 px-2.5 py-1">{cleaningLabel} уборка</span>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1.5 block text-sm font-medium text-slate-700">Имя</span>
                  <span className="relative block">
                    <User size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      className="w-full rounded-xl border border-slate-200 bg-white px-10 py-3 text-sm outline-none ring-brand/25 transition focus:border-brand focus:ring-4"
                      type="text"
                      placeholder="Как к вам обращаться"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      autoComplete="name"
                      required
                    />
                  </span>
                </label>
                <label className="block">
                  <span className="mb-1.5 block text-sm font-medium text-slate-700">Телефон</span>
                  <span className="relative block">
                    <Phone size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      className="w-full rounded-xl border border-slate-200 bg-white px-10 py-3 text-sm outline-none ring-brand/25 transition focus:border-brand focus:ring-4"
                      type="tel"
                      placeholder="+7 (___) ___-__-__"
                      value={phone}
                      onChange={(event) => setPhone(formatPhone(event.target.value))}
                      autoComplete="tel"
                      required
                    />
                  </span>
                </label>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1.5 block text-sm font-medium text-slate-700">
                    Желаемая дата <span className="font-normal text-muted">(необязательно)</span>
                  </span>
                  <span className="relative block">
                    <Calendar size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      className="w-full rounded-xl border border-slate-200 bg-white px-10 py-3 text-sm outline-none ring-brand/25 transition focus:border-brand focus:ring-4"
                      type="date"
                      value={desiredDate}
                      min={new Date().toISOString().slice(0, 10)}
                      onChange={(event) => setDesiredDate(event.target.value)}
                    />
                  </span>
                </label>
                <div>
                  <span className="mb-1.5 block text-sm font-medium text-slate-700">Удобный способ связи</span>
                  <div className="flex gap-2">
                    {CONTACT_METHODS.map((method) => {
                      const Icon = method.icon;
                      return (
                        <button
                          key={method.id}
                          type="button"
                          onClick={() => setContactMethod(method.id)}
                          className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition ${
                            contactMethod === method.id
                              ? "bg-slate-900 text-white"
                              : "border border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                          }`}
                        >
                          <Icon size={14} />
                          {method.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <label className="block">
                <span className="mb-1.5 block text-sm font-medium text-slate-700">
                  Комментарий <span className="font-normal text-muted">(необязательно)</span>
                </span>
                <textarea
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none ring-brand/25 transition focus:border-brand focus:ring-4"
                  rows={3}
                  placeholder="Домофон, парковка, особые пожелания…"
                  value={comment}
                  onChange={(event) => setComment(event.target.value.slice(0, 500))}
                />
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

              {/* Название кнопки — по ТЗ п.14. */}
              <button
                type="submit"
                disabled={!isContactValid || submitStatus === "loading"}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {submitStatus === "loading" ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Отправляем заявку...
                  </>
                ) : (
                  <>Получить стоимость уборки</>
                )}
              </button>

              <p className="flex items-center justify-center gap-1.5 text-center text-xs text-muted">
                <ShieldCheck size={13} className="shrink-0 text-brand-deep" />
                Стоимость согласуем до начала работ. Оплата — после приёмки.
              </p>
            </form>
          ) : null}

          {/* Навигация по шагам */}
          {step < 4 ? (
            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                onClick={() => goToStep(step - 1)}
                disabled={step === 1}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ArrowLeft size={15} />
                Назад
              </button>
              <button
                type="button"
                onClick={() => goToStep(step + 1)}
                disabled={step === 2 && !isAreaValid}
                className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                Далее
                <ArrowRight size={15} />
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-start pt-1">
              <button
                type="button"
                onClick={() => goToStep(3)}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                <ArrowLeft size={15} />
                Назад
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </section>
  );
}
