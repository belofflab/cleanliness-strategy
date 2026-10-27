import type { Metadata } from "next";
import { ACTIVE_CITY_SLUGS, CITY_PROFILES, DEFAULT_CITY_SLUG, type CitySlug } from "@/lib/city";
import { getSiteUrl } from "@/lib/site";

const BASE_DOMAIN = "cleanliness.pro";

function normalizePath(pathname: string) {
  if (!pathname) return "/";
  const withLeadingSlash = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return withLeadingSlash === "/" ? "/" : withLeadingSlash.replace(/\/$/, "");
}

function isDevelopmentSite(origin: string) {
  return origin.includes("localhost") || origin.includes("127.0.0.1");
}

function getProductionOrigin(citySlug: CitySlug) {
  return citySlug === DEFAULT_CITY_SLUG ? `https://${BASE_DOMAIN}` : `https://${citySlug}.${BASE_DOMAIN}`;
}

function getDevelopmentCanonicalUrl(citySlug: CitySlug, pathname: string) {
  const baseOrigin = new URL(getSiteUrl()).origin;
  const safePath = normalizePath(pathname);

  if (citySlug === DEFAULT_CITY_SLUG) {
    return `${baseOrigin}${safePath === "/" ? "" : safePath}`;
  }

  return `${baseOrigin}/${citySlug}${safePath === "/" ? "" : safePath}`;
}

export function getCityCanonicalUrl(citySlug: CitySlug, pathname = "/") {
  const baseOrigin = new URL(getSiteUrl()).origin;
  const safePath = normalizePath(pathname);

  if (isDevelopmentSite(baseOrigin)) {
    return getDevelopmentCanonicalUrl(citySlug, safePath);
  }

  const origin = getProductionOrigin(citySlug);
  return `${origin}${safePath === "/" ? "" : safePath}`;
}

export function getCityHreflangMap(pathname = "/") {
  const languages: Record<string, string> = {};
  for (const citySlug of ACTIVE_CITY_SLUGS) {
    languages[`ru-RU-x-${citySlug}`] = getCityCanonicalUrl(citySlug, pathname);
  }
  languages["x-default"] = getCityCanonicalUrl(DEFAULT_CITY_SLUG, pathname);
  return languages;
}

export function buildCityMetadata(citySlug: CitySlug): Metadata {
  const city = CITY_PROFILES[citySlug];
  const canonical = getCityCanonicalUrl(citySlug, "/");

  return {
    // Коммерческий интент («клининг + город») в начале title — базовый фактор
    // релевантности локальной выдачи. Бренд добавит root-шаблон «%s | Точка Чистоты».
    title: `Клининг ${city.namePrepositional} — уборка квартир и офисов`,
    description: `Клининговая компания ${city.namePrepositional}: поддерживающая и генеральная уборка, после ремонта, офисы. Свои средства, выезд в день заявки, оплата после приёмки. Онлайн-расчёт за минуту.`,
    keywords: [
      `клининг ${city.name}`,
      `клининговая компания ${city.name}`,
      `уборка квартиры ${city.name}`,
      `генеральная уборка ${city.name}`,
      `уборка после ремонта ${city.name}`,
      `уборка офисов ${city.name}`,
      `мытьё окон ${city.name}`,
      "Точка Чистоты",
    ],
    alternates: {
      canonical,
      languages: getCityHreflangMap("/"),
    },
    openGraph: {
      title: `Точка Чистоты — Премиальный клининг ${city.namePrepositional}`,
      description: `Современный клининговый сервис ${city.namePrepositional}: прозрачная цена, быстрый выезд и контроль качества.`,
      type: "website",
      locale: "ru_RU",
      url: canonical,
      siteName: "Точка Чистоты",
    },
    twitter: {
      card: "summary_large_image",
      title: `Точка Чистоты — Уборка ${city.namePrepositional}`,
      description: `Быстрый расчёт стоимости уборки ${city.namePrepositional}, быстрый выезд и удобная связь с менеджером.`,
    },
  };
}

export function getRegionalSitemapUrls() {
  return ACTIVE_CITY_SLUGS.map((citySlug) => getCityCanonicalUrl(citySlug, "/sitemap.xml"));
}

export function getRegionalLandingEntries() {
  return ACTIVE_CITY_SLUGS.map((citySlug) => ({
    citySlug,
    url: getCityCanonicalUrl(citySlug, "/"),
  }));
}
