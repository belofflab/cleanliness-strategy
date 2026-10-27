"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { BadgeCheck, ShieldCheck, Sparkles, TimerReset } from "lucide-react";
import { trackEvent } from "@/lib/analytics";
import {
  DEFAULT_CITY_SLUG,
  getCityProfile,
  getCitySlugFromHost,
  getCitySlugFromPathname,
  normalizeCitySlug,
  writeCitySlugCookie,
} from "@/lib/city";
import { captureAttributionFromBrowser, getMultilandingHeadline } from "@/lib/attribution";
import CallbackModal from "@/components/CallbackModal";
import CitySelectorModal from "@/components/CitySelectorModal";
import Hero from "@/components/Hero";
import Logo from "@/components/Logo";
import ProcessSection from "@/components/ProcessSection";
import QuizCalculator from "@/components/QuizCalculator";

// Секции ниже первого экрана грузим отдельными чанками (ТЗ п.11 — скорость):
// SSR-разметка сохраняется, а первичный JS-бандл становится заметно легче.
const TeamSection = dynamic(() => import("@/components/TeamSection"));
const SafetySection = dynamic(() => import("@/components/SafetySection"));
const CasesSection = dynamic(() => import("@/components/CasesSection"));
const ReviewsSection = dynamic(() => import("@/components/ReviewsSection"));
const PreparationSection = dynamic(() => import("@/components/PreparationSection"));
const FaqSection = dynamic(() => import("@/components/FaqSection"));
const CtaSection = dynamic(() => import("@/components/CtaSection"));
const Footer = dynamic(() => import("@/components/Footer"));
const CookieBanner = dynamic(() => import("@/components/CookieBanner"), { ssr: false });

// href — SEO-посадочные услуг (перелинковка с главной усиливает их в выдаче).
const SERVICES = [
  {
    title: "Поддерживающая уборка",
    description: "Регулярный уход за квартирой или офисом по удобному графику.",
    href: "/uborka-kvartir",
  },
  {
    title: "Генеральная уборка",
    description: "Глубокая очистка сложных зон, техники и труднодоступных поверхностей.",
    href: "/generalnaya-uborka",
  },
  {
    title: "После ремонта",
    description: "Удаление строительной пыли и следов работ без риска для отделки.",
    href: "/uborka-posle-remonta",
  },
  {
    title: "Мытьё окон",
    description: "Стёкла без разводов, рамы, откосы и балконное остекление — цена за створку.",
    href: "/mytie-okon",
  },
  {
    title: "Офисная уборка",
    description: "Кабинеты, open space и санузлы — разово или по регулярному графику.",
    href: "/#calculator",
  },
];

const BENEFITS = [
  {
    title: "Контроль качества",
    description: "Чек-листы, фотофиксация результата и единые стандарты сервиса.",
    icon: ShieldCheck,
  },
  {
    title: "Быстрый выезд",
    description: "Подтверждаем заявку в течение 7 минут и согласуем удобное окно.",
    icon: TimerReset,
  },
  {
    title: "Премиум-сервис",
    description: "Вежливая команда, аккуратный инвентарь и технологичный клиентский путь.",
    icon: Sparkles,
  },
  {
    title: "Прозрачная цена",
    description: "Без скрытых доплат: расчет стоимости до начала работ.",
    icon: BadgeCheck,
  },
];

function getPathWithoutCity(pathname) {
  const normalizedPath = pathname || "/";
  return getCitySlugFromPathname(normalizedPath)
    ? normalizedPath.replace(/^\/[^/]+/, "") || "/"
    : normalizedPath;
}

function getCityPath(citySlug, pathname) {
  const pathWithoutCity = getPathWithoutCity(pathname);
  return `/${citySlug}${pathWithoutCity === "/" ? "" : pathWithoutCity}`;
}

/**
 * @param {{ initialCitySlug?: import("@/lib/city").CitySlug }} props
 */
export default function App({ initialCitySlug = DEFAULT_CITY_SLUG }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [requestContext, setRequestContext] = useState("");
  const [attribution] = useState(() =>
    typeof window === "undefined" ? {} : captureAttributionFromBrowser()
  );
  const [citySlug, setCitySlug] = useState(() => {
    if (typeof window === "undefined") {
      return normalizeCitySlug(initialCitySlug);
    }

    const cityFromPath = getCitySlugFromPathname(window.location.pathname);
    const cityFromHost = getCitySlugFromHost(window.location.host);
    return normalizeCitySlug(cityFromPath ?? cityFromHost ?? initialCitySlug);
  });
  // Состояние «проскроллено» — для уплотнения и тени липкой шапки.
  const [scrolled, setScrolled] = useState(false);
  const cityProfile = getCityProfile(citySlug);
  const heroHeadline = getMultilandingHeadline(attribution.utm_campaign, cityProfile.namePrepositional);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    // passive — не блокируем скролл, плавнее на мобильных.
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    writeCitySlugCookie(citySlug);
  }, [citySlug]);

  const openCallback = (context = "") => {
    trackEvent("callback_open", {
      context,
      city_slug: citySlug,
      utm_campaign: attribution.utm_campaign,
      yclid: attribution.yclid,
    });
    setRequestContext(context);
    setIsModalOpen(true);
  };

  const handleCitySelect = (nextCitySlug) => {
    const resolvedNextCity = normalizeCitySlug(nextCitySlug);
    if (resolvedNextCity === citySlug) return;

    writeCitySlugCookie(resolvedNextCity);
    setCitySlug(resolvedNextCity);
    trackEvent("city_change", {
      city_slug: resolvedNextCity,
      utm_campaign: attribution.utm_campaign,
    });

    const { hostname, protocol, search, hash } = window.location;
    const currentPathname = pathname ?? window.location.pathname;
    const isBlanqDomain = hostname === "cleanliness.pro" || hostname.endsWith(".cleanliness.pro");
    const targetPath = getCityPath(resolvedNextCity, currentPathname);

    if (isBlanqDomain) {
      const targetHost =
        resolvedNextCity === DEFAULT_CITY_SLUG ? "cleanliness.pro" : `${resolvedNextCity}.cleanliness.pro`;
      window.location.assign(`${protocol}//${targetHost}${targetPath}${search}${hash}`);
      return;
    }

    router.replace(`${targetPath}${search}${hash}`, { scroll: false });
  };

  return (
    <div className="min-h-screen scroll-smooth bg-background text-foreground">
      <header
        className={`sticky top-0 z-30 border-b backdrop-blur-xl transition-[padding,box-shadow,background-color,border-color] duration-300 ${
          scrolled
            ? "border-slate-200/70 bg-background/80 py-2 shadow-lg shadow-slate-900/5"
            : "border-white/30 bg-background/60 py-3"
        } px-4 sm:px-6 lg:px-10`}
      >
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3">
          <Link href="#hero" aria-label="Точка Чистоты — на главную">
            <Logo size={32} textClassName="text-lg text-slate-950" />
          </Link>
          <nav className="hidden items-center gap-5 text-sm font-medium text-slate-700 sm:flex">
            <Link href="#services" className="transition hover:text-brand-deep">
              Услуги
            </Link>
            <Link href="#calculator" className="transition hover:text-brand-deep">
              Расчёт стоимости
            </Link>
            <Link href="#before-after" className="transition hover:text-brand-deep">
              Кейсы
            </Link>
            <Link href="#reviews" className="transition hover:text-brand-deep">
              Отзывы
            </Link>
            <Link href="#faq" className="transition hover:text-brand-deep">
              FAQ
            </Link>
            <Link href="#contacts" className="transition hover:text-brand-deep">
              Контакты
            </Link>
          </nav>
          <div className="flex items-center gap-2">
            <CitySelectorModal currentCitySlug={citySlug} onSelectCity={handleCitySelect} />
            <button
              type="button"
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
              onClick={() => openCallback("Запрос из шапки")}
            >
              Заказать звонок
            </button>
          </div>
        </div>
      </header>

      <main>
        <Hero
          onOpenCallback={openCallback}
          cityName={cityProfile.name}
          cityNamePrepositional={cityProfile.namePrepositional}
          cityPhone={cityProfile.phone}
          headline={heroHeadline}
        />

        <section id="services" className="px-4 py-16 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-6xl rounded-4xl border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
            <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
              Услуги
            </h2>
            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {SERVICES.map((service) => (
                <Link
                  key={service.title}
                  href={service.href}
                  className="group rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:shadow-md"
                >
                  <h3 className="font-display text-lg font-semibold text-slate-900">{service.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{service.description}</p>
                  <span className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-brand-deep">
                    Подробнее
                    <span className="transition group-hover:translate-x-0.5">→</span>
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <QuizCalculator citySlug={citySlug} attribution={attribution} />
        <ProcessSection />

        {/* «Наша команда» — перед блоком «Почему нам доверяют» (ТЗ п.9.1). */}
        <TeamSection citySlug={citySlug} />

        <section id="advantages" className="px-4 py-16 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-6xl rounded-4xl border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
            <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
              Почему нам доверяют
            </h2>
            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {BENEFITS.map((benefit, index) => {
                const Icon = benefit.icon;

                return (
                  <motion.article
                    key={benefit.title}
                    initial={{ opacity: 0, y: 14 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.4 }}
                    transition={{ duration: 0.3, delay: index * 0.06 }}
                    className="rounded-2xl border border-slate-200 bg-white p-5"
                  >
                    <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                      <Icon size={18} />
                    </span>
                    <h3 className="mt-3 font-display text-lg font-semibold text-slate-900">{benefit.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted">{benefit.description}</p>
                  </motion.article>
                );
              })}
            </div>
          </div>
        </section>

        {/* «Безопасность и гарантия результата» — после блока преимуществ (ТЗ п.9.2). */}
        <SafetySection />

        <CasesSection citySlug={citySlug} />
        <ReviewsSection citySlug={citySlug} />

        {/* «Подготовка к приезду клинеров» — перед FAQ (ТЗ п.9.4). */}
        <PreparationSection />

        <FaqSection />
        <CtaSection onOpenCallback={openCallback} />
        <Footer onOpenCallback={openCallback} cityProfile={cityProfile} />
      </main>

      <CallbackModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        contextText={requestContext}
        citySlug={citySlug}
        attribution={attribution}
      />

      <CookieBanner />
    </div>
  );
}
