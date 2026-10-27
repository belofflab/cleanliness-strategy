const ATTRIBUTION_STORAGE_KEY = "blanq_attribution_v1";
const ATTRIBUTION_COOKIE_KEY = "blanq_attribution";
const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

export type LeadAttribution = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  yclid?: string;
  gclid?: string;
  ym_uid?: string;
};

const CAMPAIGN_H1_MAP: Record<string, string> = {
  уборка_после_ремонта: "Уборка после ремонта под ключ — аккуратно и без строительной пыли",
  генеральная_уборка: "Генеральная уборка с контролем качества в каждом помещении",
  поддерживающая_уборка: "Регулярная уборка по удобному графику без переплат",
};

function removeEmpty(data: LeadAttribution): LeadAttribution {
  return Object.entries(data).reduce<LeadAttribution>((acc, [key, value]) => {
    if (typeof value === "string" && value.trim()) {
      acc[key as keyof LeadAttribution] = value.trim();
    }
    return acc;
  }, {});
}

function parseJson(value: string | null): LeadAttribution {
  if (!value) return {};
  try {
    return removeEmpty(JSON.parse(value));
  } catch {
    return {};
  }
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;

  const token = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`));

  return token ? decodeURIComponent(token.split("=").slice(1).join("=")) : null;
}

function writeCookie(name: string, value: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${ONE_YEAR_SECONDS}; SameSite=Lax`;
}

function readYmUid(): string | undefined {
  if (typeof window === "undefined") return undefined;

  const ymFromCookie = readCookie("_ym_uid");
  if (ymFromCookie) {
    window.localStorage?.setItem("_ym_uid", ymFromCookie);
    return ymFromCookie;
  }

  return window.localStorage?.getItem("_ym_uid") || undefined;
}

export function readStoredAttribution(): LeadAttribution {
  if (typeof window === "undefined") return {};

  const fromStorage = parseJson(window.localStorage?.getItem(ATTRIBUTION_STORAGE_KEY) || null);
  const fromCookie = parseJson(readCookie(ATTRIBUTION_COOKIE_KEY));
  return removeEmpty({ ...fromCookie, ...fromStorage });
}

export function parseAttributionFromSearch(search: string): LeadAttribution {
  const params = new URLSearchParams(search);

  return removeEmpty({
    utm_source: params.get("utm_source") || undefined,
    utm_medium: params.get("utm_medium") || undefined,
    utm_campaign: params.get("utm_campaign") || undefined,
    utm_content: params.get("utm_content") || undefined,
    utm_term: params.get("utm_term") || undefined,
    yclid: params.get("yclid") || undefined,
    gclid: params.get("gclid") || undefined,
    ym_uid: params.get("_ym_uid") || undefined,
  });
}

export function captureAttributionFromBrowser(): LeadAttribution {
  if (typeof window === "undefined") return {};

  const fromStorage = readStoredAttribution();
  const fromSearch = parseAttributionFromSearch(window.location.search);
  const ymUid = fromSearch.ym_uid || fromStorage.ym_uid || readYmUid();

  const merged = removeEmpty({
    ...fromStorage,
    ...fromSearch,
    ym_uid: ymUid,
  });

  window.localStorage?.setItem(ATTRIBUTION_STORAGE_KEY, JSON.stringify(merged));
  writeCookie(ATTRIBUTION_COOKIE_KEY, JSON.stringify(merged));

  if (merged.ym_uid) {
    window.localStorage?.setItem("_ym_uid", merged.ym_uid);
  }

  return merged;
}

export function getMultilandingHeadline(campaign: string | null | undefined, fallbackCityText: string) {
  // Базовый H1 по ТЗ (п.7): конкретно и понятно — что убираем, для кого и где.
  if (!campaign) {
    return `Профессиональная уборка квартир и офисов ${fallbackCityText}`;
  }

  return CAMPAIGN_H1_MAP[campaign] || `Профессиональная уборка квартир и офисов ${fallbackCityText}`;
}

export function toLeadPayloadAttribution(attribution: LeadAttribution) {
  const cleaned = removeEmpty(attribution);
  const utm = {
    source: cleaned.utm_source,
    medium: cleaned.utm_medium,
    campaign: cleaned.utm_campaign,
    content: cleaned.utm_content,
    term: cleaned.utm_term,
  };
  const normalizedUtm = Object.fromEntries(
    Object.entries(utm).filter(([, value]) => typeof value === "string" && value.trim())
  );

  return {
    utm: normalizedUtm,
    yclid: cleaned.yclid || null,
    gclid: cleaned.gclid || null,
    ym_uid: cleaned.ym_uid || null,
  };
}
