const ONE_YEAR_IN_SECONDS = 60 * 60 * 24 * 365;

export const CITY_COOKIE_NAME = "city_slug";

// Все известные городá (типы, профили, исторические данные CRM).
export const CITY_SLUGS = ["tyumen", "ufa"] as const;

export type CitySlug = (typeof CITY_SLUGS)[number];

// Бизнес стартует с Уфы (август 2026): Уфа — город по умолчанию, реклама и
// звонки идут туда. Тюменский лендинг ОСТАЁТСЯ активным и индексируемым —
// SEO-прогрев под будущий запуск, заявки из Тюмени принимаются в CRM.
export const ACTIVE_CITY_SLUGS: readonly CitySlug[] = ["tyumen", "ufa"];
export const DEFAULT_CITY_SLUG: CitySlug = "ufa";

export type ReviewPlatform = {
  /** Название площадки («Яндекс», «2ГИС»). */
  name: string;
  /** Текущая оценка на площадке («5,0»). Показываем только реальные значения. */
  rating: string;
  /** Ссылка на профиль компании (карточка рейтинга и «Смотреть оригинал»). */
  url: string;
};

type CityProfile = {
  slug: CitySlug;
  name: string;
  namePrepositional: string;
  phone: string;
  email: string;
  locality: string;
  primaryBranchAddress: string;
  workingHours: string;
  /** Районы выезда — блок контактов (ТЗ п.9.5). */
  districts: string[];
  /** Условия выезда за пределы города. */
  outOfCityNote: string;
  /** Встроенная Яндекс Карта (iframe src). */
  mapEmbedSrc: string;
  /** Кнопка «Построить маршрут». */
  routeUrl: string;
  /** Профиль в Яндекс Бизнес / на Картах. */
  yandexBusinessUrl: string;
  /** Профиль в 2ГИС. */
  twoGisUrl: string;
  /**
   * Карточки рейтингов в блоке отзывов (ТЗ п.6). Выводятся только заполненные;
   * если подтверждаемого профиля нет — уберите элемент из списка.
   */
  reviewPlatforms: ReviewPlatform[];
};

// Роутинг (пути/поддомены/куки) принимает только АКТИВНЫЕ города:
// «/tyumen» и tyumen-поддомен при отключённом городе ведут на город по умолчанию.
const CITY_SLUG_SET = new Set<string>(ACTIVE_CITY_SLUGS);
const KNOWN_CITY_SLUG_SET = new Set<string>(CITY_SLUGS);

/** Город известен системе (в т.ч. временно отключённый) — для редиректов. */
export function isKnownCitySlug(value: string | null | undefined): value is CitySlug {
  const normalized = normalizeRawSlug(value);
  return normalized !== null && KNOWN_CITY_SLUG_SET.has(normalized);
}

export const CITY_PROFILES: Record<CitySlug, CityProfile> = {
  tyumen: {
    slug: "tyumen",
    name: "Тюмень",
    namePrepositional: "в Тюмени",
    phone: "+7 (912) 395-20-43",
    email: "ow@blanq.tech",
    locality: "Тюмень",
    primaryBranchAddress: "ул. Республики, 55",
    workingHours: "Ежедневно 08:00–22:00",
    districts: [
      "Центральный округ",
      "Калининский округ",
      "Ленинский округ",
      "Восточный округ",
      "Заречные микрорайоны",
      "Дом Обороны",
    ],
    outOfCityNote:
      "Выезжаем в пригород Тюмени по договорённости — стоимость выезда согласуем при подтверждении заказа.",
    mapEmbedSrc:
      "https://yandex.ru/map-widget/v1/?text=%D0%A2%D1%8E%D0%BC%D0%B5%D0%BD%D1%8C%2C%20%D1%83%D0%BB%D0%B8%D1%86%D0%B0%20%D0%A0%D0%B5%D1%81%D0%BF%D1%83%D0%B1%D0%BB%D0%B8%D0%BA%D0%B8%2C%2055&z=15",
    routeUrl:
      "https://yandex.ru/maps/?rtext=~%D0%A2%D1%8E%D0%BC%D0%B5%D0%BD%D1%8C%2C%20%D1%83%D0%BB%D0%B8%D1%86%D0%B0%20%D0%A0%D0%B5%D1%81%D0%BF%D1%83%D0%B1%D0%BB%D0%B8%D0%BA%D0%B8%2C%2055",
    yandexBusinessUrl: "https://yandex.ru/profile/38819697230",
    twoGisUrl:
      "https://2gis.ru/tyumen/search/%D0%A2%D0%BE%D1%87%D0%BA%D0%B0%20%D0%A7%D0%B8%D1%81%D1%82%D0%BE%D1%82%D1%8B",
    reviewPlatforms: [
      {
        name: "Яндекс",
        rating: "5,0",
        url: "https://yandex.ru/profile/38819697230",
      },
      {
        name: "2ГИС",
        rating: "5,0",
        url: "https://2gis.ru/tyumen/search/%D0%A2%D0%BE%D1%87%D0%BA%D0%B0%20%D0%A7%D0%B8%D1%81%D1%82%D0%BE%D1%82%D1%8B",
      },
    ],
  },
  ufa: {
    slug: "ufa",
    name: "Уфа",
    namePrepositional: "в Уфе",
    phone: "+7 (993) 138-50-53",
    email: "ow@blanq.tech",
    locality: "Уфа",
    primaryBranchAddress: "пр. Октября, 56",
    workingHours: "Ежедневно 08:00–22:00",
    districts: [
      "Кировский район",
      "Ленинский район",
      "Советский район",
      "Октябрьский район",
      "Орджоникидзевский район",
      "Сипайлово и Зелёная Роща",
    ],
    outOfCityNote:
      "Выезжаем в пригород Уфы по договорённости — стоимость выезда согласуем при подтверждении заказа.",
    mapEmbedSrc:
      "https://yandex.ru/map-widget/v1/?text=%D0%A3%D1%84%D0%B0%2C%20%D0%BF%D1%80%D0%BE%D1%81%D0%BF%D0%B5%D0%BA%D1%82%20%D0%9E%D0%BA%D1%82%D1%8F%D0%B1%D1%80%D1%8F%2C%2056&z=15",
    routeUrl:
      "https://yandex.ru/maps/?rtext=~%D0%A3%D1%84%D0%B0%2C%20%D0%BF%D1%80%D0%BE%D1%81%D0%BF%D0%B5%D0%BA%D1%82%20%D0%9E%D0%BA%D1%82%D1%8F%D0%B1%D1%80%D1%8F%2C%2056",
    yandexBusinessUrl: "https://yandex.ru/profile/38819697230",
    twoGisUrl:
      "https://2gis.ru/ufa/search/%D0%A2%D0%BE%D1%87%D0%BA%D0%B0%20%D0%A7%D0%B8%D1%81%D1%82%D0%BE%D1%82%D1%8B",
    reviewPlatforms: [
      {
        name: "Яндекс",
        rating: "5,0",
        url: "https://yandex.ru/profile/38819697230",
      },
      {
        name: "2ГИС",
        rating: "5,0",
        url: "https://2gis.ru/ufa/search/%D0%A2%D0%BE%D1%87%D0%BA%D0%B0%20%D0%A7%D0%B8%D1%81%D1%82%D0%BE%D1%82%D1%8B",
      },
    ],
  },
};

function removePort(host: string) {
  return host.replace(/:\d+$/, "").trim().toLowerCase();
}

function normalizeRawSlug(value: string | null | undefined): string | null {
  const normalized = value?.trim().toLowerCase() ?? "";
  return normalized || null;
}

export function isCitySlug(value: string | null | undefined): value is CitySlug {
  const normalized = normalizeRawSlug(value);
  return normalized !== null && CITY_SLUG_SET.has(normalized);
}

export function normalizeCitySlug(value: string | null | undefined): CitySlug {
  return isCitySlug(value) ? value : DEFAULT_CITY_SLUG;
}

export function getCitySlugFromPathname(pathname: string | null | undefined): CitySlug | null {
  if (!pathname) return null;
  const firstSegment = pathname.split("/").filter(Boolean)[0];
  return isCitySlug(firstSegment) ? firstSegment : null;
}

export function getCitySlugFromHost(host: string | null | undefined): CitySlug | null {
  if (!host) return null;

  const normalizedHost = removePort(host).replace(/\.$/, "");
  if (!normalizedHost) return null;

  if (normalizedHost === "cleanliness.pro" || normalizedHost === "www.cleanliness.pro") {
    return DEFAULT_CITY_SLUG;
  }

  if (normalizedHost.endsWith(".cleanliness.pro")) {
    const subdomain = normalizedHost.slice(0, -".cleanliness.pro".length).split(".").at(-1);
    return isCitySlug(subdomain) ? subdomain : null;
  }

  if (normalizedHost.endsWith(".localhost")) {
    const localSubdomain = normalizedHost.slice(0, -".localhost".length).split(".").at(-1);
    return isCitySlug(localSubdomain) ? localSubdomain : null;
  }

  return null;
}

export function readCitySlugCookie(): CitySlug | null {
  if (typeof document === "undefined") return null;

  const token = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${CITY_COOKIE_NAME}=`));

  if (!token) return null;

  const value = token.split("=").slice(1).join("=");
  return isCitySlug(value) ? value : null;
}

export function writeCitySlugCookie(citySlug: CitySlug) {
  if (typeof document === "undefined") return;
  document.cookie = `${CITY_COOKIE_NAME}=${citySlug}; Path=/; Max-Age=${ONE_YEAR_IN_SECONDS}; SameSite=Lax`;
}

export function getCityProfile(citySlug: string | null | undefined) {
  const slug = normalizeCitySlug(citySlug);
  return CITY_PROFILES[slug];
}
