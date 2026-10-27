// SEO-посадочная услуги (фаза 2): серверный рендер без клиентского JS —
// быстрый LCP, весь контент виден поисковикам. CTA ведут на квиз главной
// страницы города и на телефон города.

import Link from "next/link";
import {
  ArrowRight,
  Check,
  ChevronDown,
  Clock3,
  PhoneCall,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Logo from "@/components/Logo";
import { getCityProfile, type CitySlug } from "@/lib/city";
import { SERVICE_LANDINGS, type ServiceLanding } from "@/lib/service-landings";

function toPhoneHref(phone: string) {
  return `tel:${phone.replace(/[^\d+]/g, "")}`;
}

const TRUST_POINTS = [
  { icon: Clock3, text: "Ответим до 7 минут, работаем ежедневно 08:00–22:00" },
  { icon: ShieldCheck, text: "Цена фиксируется до начала работ, оплата после приёмки" },
  { icon: Sparkles, text: "Свои профессиональные средства и инвентарь" },
];

export default function ServiceLandingView({
  citySlug,
  service,
}: {
  citySlug: CitySlug;
  service: ServiceLanding;
}) {
  const city = getCityProfile(citySlug);
  const phoneHref = toPhoneHref(city.phone);
  const priceFrom = service.priceFrom[citySlug];
  const otherServices = SERVICE_LANDINGS.filter((item) => item.slug !== service.slug);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Компактная шапка посадочной: логотип → главная города, телефон, CTA. */}
      <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-background/85 px-4 py-3 backdrop-blur-xl sm:px-6 lg:px-10">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-3">
          <Link href="/" aria-label="Точка Чистоты — на главную">
            <Logo size={30} textClassName="text-base text-slate-950" />
          </Link>
          <div className="flex items-center gap-2">
            <a
              href={phoneHref}
              className="hidden text-sm font-semibold text-slate-800 transition hover:text-brand-deep sm:block"
            >
              {city.phone}
            </a>
            <Link
              href="/#calculator"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Рассчитать стоимость
            </Link>
          </div>
        </div>
      </header>

      <main className="px-4 pb-16 sm:px-6 lg:px-10">
        {/* Hero */}
        <section className="mx-auto w-full max-w-5xl pt-10">
          <p className="inline-flex rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-brand-deep">
            Точка Чистоты • {city.name}
          </p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-semibold leading-tight tracking-tight text-slate-950 sm:text-5xl">
            {service.name} {city.namePrepositional}
          </h1>
          <div className="mt-4 max-w-2xl space-y-3">
            {service.intro.map((paragraph) => (
              <p key={paragraph.slice(0, 24)} className="text-base leading-relaxed text-muted sm:text-lg">
                {paragraph}
              </p>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link
              href="/#calculator"
              className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Рассчитать стоимость
              <ArrowRight size={16} />
            </Link>
            <a
              href={phoneHref}
              className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3.5 text-sm font-semibold text-slate-800 transition hover:border-slate-300 hover:bg-slate-50"
            >
              <PhoneCall size={16} />
              {city.phone}
            </a>
          </div>

          <ul className="mt-6 grid gap-2 sm:grid-cols-3">
            {TRUST_POINTS.map((point) => {
              const Icon = point.icon;
              return (
                <li
                  key={point.text}
                  className="flex items-start gap-2 rounded-2xl border border-slate-200 bg-white p-3 text-sm text-slate-700"
                >
                  <Icon size={16} className="mt-0.5 shrink-0 text-brand-deep" />
                  {point.text}
                </li>
              );
            })}
          </ul>
        </section>

        {/* Что входит */}
        <section className="mx-auto mt-12 w-full max-w-5xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 md:p-10">
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Что входит в услугу
          </h2>
          <ul className="mt-6 grid gap-3 sm:grid-cols-2">
            {service.includes.map((item) => (
              <li key={item} className="flex items-start gap-2.5 rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-700">
                <Check size={16} className="mt-0.5 shrink-0 text-emerald-600" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        {/* Цена */}
        <section className="mx-auto mt-8 w-full max-w-5xl rounded-[2rem] border border-sky-200 bg-gradient-to-r from-sky-50 to-cyan-50 p-6 md:p-10">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.13em] text-slate-500">
                Стоимость {city.namePrepositional}
              </p>
              <p className="mt-2 font-display text-4xl font-semibold text-slate-950">
                от {priceFrom.toLocaleString("ru-RU")} ₽
              </p>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-700">{service.priceNote}</p>
            </div>
            <Link
              href="/#calculator"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Получить стоимость уборки
              <ArrowRight size={16} />
            </Link>
          </div>
        </section>

        {/* FAQ услуги: details/summary — интерактивность без клиентского JS. */}
        <section className="mx-auto mt-8 w-full max-w-5xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 md:p-10">
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Частые вопросы
          </h2>
          <div className="mt-6 space-y-3">
            {service.faq.map((item) => (
              <details key={item.question} className="group rounded-2xl border border-slate-200 bg-white">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-4 text-sm font-semibold text-slate-900 sm:text-base [&::-webkit-details-marker]:hidden">
                  {item.question}
                  <ChevronDown size={18} className="shrink-0 text-slate-500 transition group-open:rotate-180" />
                </summary>
                <p className="px-4 pb-4 text-sm leading-relaxed text-muted">{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        {/* Перелинковка */}
        <section className="mx-auto mt-8 w-full max-w-5xl">
          <h2 className="font-display text-xl font-semibold tracking-tight text-slate-900">
            Другие услуги {city.namePrepositional}
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {otherServices.map((item) => (
              <Link
                key={item.slug}
                href={`/${item.slug}`}
                className="group rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-slate-300 hover:shadow-md"
              >
                <p className="font-display text-base font-semibold text-slate-900">
                  {item.name} {city.namePrepositional}
                </p>
                <p className="mt-1 text-sm text-muted">
                  от {item.priceFrom[citySlug].toLocaleString("ru-RU")} ₽
                </p>
                <span className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-brand-deep">
                  Подробнее
                  <ArrowRight size={14} className="transition group-hover:translate-x-0.5" />
                </span>
              </Link>
            ))}
          </div>
          <Link
            href="/"
            className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-brand-deep"
          >
            ← Все услуги и расчёт стоимости на главной
          </Link>
        </section>
      </main>

      <footer className="border-t border-slate-200 px-4 py-6 sm:px-6">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-3 text-xs text-muted">
          <p>ООО «ОМ» · ИНН 0273955232 · {city.locality}, {city.primaryBranchAddress}</p>
          <p className="flex gap-3">
            <Link href="/oferta" className="transition hover:text-brand-deep">Оферта</Link>
            <Link href="/privacy" className="transition hover:text-brand-deep">Конфиденциальность</Link>
          </p>
        </div>
      </footer>
    </div>
  );
}
