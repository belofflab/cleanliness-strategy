// Типизированный клиент backend API «Точка Чистоты».
// База берётся из NEXT_PUBLIC_API_URL (бандлится в браузер, см. docs/environment-variables.md).
// Все методы — с graceful-обработкой: при недоступном бэкенде вызывающий код
// может откатиться на локальный расчёт, чтобы лендинг работал даже без API.

import { DEFAULT_CITY_SLUG } from "@/lib/city";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000/api/v1";

// Жёсткий таймаут запросов: зависший бэкенд не должен подвешивать интерфейс
// (ТЗ п.11 — стабильность загрузки; фоллбэк на локальный расчёт срабатывает быстро).
const REQUEST_TIMEOUT_MS = 10_000;

// ---------- Типы запросов/ответов ----------
export interface QuoteAddonIn {
  code: string;
  qty: number;
}

export interface QuoteRequest {
  city_slug: string;
  service_type: string; // maintenance | general | post_renovation | office
  rooms: number;
  bathrooms: number;
  /** Площадь, м² (квиз, шаг 2). Влияет на тарифы «от м²» (офисная уборка). */
  area_sqm?: number | null;
  /** Состояние: normal | neglected | heavy | needs_assessment (квиз, шаг 4). */
  condition?: string | null;
  /** Тип объекта: apartment | house | office | other (квиз, шаг 1). */
  object_type?: string | null;
  addon_codes: string[];
  /** Доп.услуги с количеством (створки, часы, штуки). */
  addons?: QuoteAddonIn[];
  promo_code?: string | null;
}

export interface QuoteLineItem {
  label: string;
  amount: number;
}

export interface QuoteResponse {
  city: string;
  service: string;
  currency: string;
  items: QuoteLineItem[];
  subtotal: number;
  discount: number;
  total: number;
  est_minutes: number;
  est_time_human: string;
  /** true — нужна предварительная оценка по фото, цена показывается как «от». */
  needs_assessment?: boolean;
}

export interface LeadRequest {
  name: string;
  phone: string;
  city_slug?: string;
  source?: string;
  context?: string | null;
  /** Итог расчёта квиза → ориентир бюджета для менеджера в CRM. */
  price?: number | null;
  /** Вид услуги (сегментация CRM). */
  service_type?: string | null;
  utm?: {
    source?: string;
    medium?: string;
    campaign?: string;
    content?: string;
    term?: string;
  } | null;
  yclid?: string | null;
  gclid?: string | null;
  ym_uid?: string | null;
}

export interface LeadResponse {
  id: string;
  status: string;
  message: string;
}

export interface Slot {
  id: string;
  master_id: string;
  master_name: string;
  work_date: string;
  start_time: string;
  end_time: string;
}

export interface BookingRequest {
  name: string;
  phone: string;
  city_slug: string;
  service_type: string;
  rooms: number;
  bathrooms: number;
  addon_codes: string[];
  promo_code?: string | null;
  schedule_id?: string | null;
  source?: string;
}

export interface BookingResponse {
  order_id: string;
  lead_id: string;
  city: string;
  service: string;
  master_name: string | null;
  work_date: string | null;
  start_time: string | null;
  total: number;
  est_minutes: number;
  est_time_human: string;
  status: string;
  message: string;
}

export interface Review {
  id: string;
  author_name: string;
  rating: number;
  text: string;
  provider: string;
  avatar_url?: string | null;
  /** Ссылка на оригинал отзыва на площадке («Смотреть оригинал»). */
  source_url?: string | null;
  /** Вид заказанной уборки. */
  service_type?: string | null;
  published_at?: string | null;
}

export interface BeforeAfterCase {
  id: string;
  title: string | null;
  before_url: string;
  after_url: string;
  // Карточка кейса (ТЗ п.4/9)
  room_type?: string | null;
  area_sqm?: number | null;
  cleaning_type?: string | null;
  cleaners_count?: number | null;
  duration_hours?: number | null;
  cost_text?: string | null;
  district?: string | null;
  task_text?: string | null;
  review_text?: string | null;
}

/** @deprecated старое имя — используйте BeforeAfterCase */
export type BeforeAfterPair = BeforeAfterCase;

export interface CatalogService {
  type: string;
  name: string;
  base_price: number;
  price_per_room: number;
  price_per_bathroom: number;
  price_per_sqm?: number;
}

export interface CatalogAddon {
  code: string;
  name: string;
  price: number;
  unit?: string | null;
  max_qty?: number;
}

export interface CityCatalog {
  city: { slug: string; name: string; price_multiplier: number };
  services: CatalogService[];
  addons: CatalogAddon[];
}

// ---------- Базовый fetch-обёртчик ----------
class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function withTimeout(signal?: AbortSignal): AbortSignal | undefined {
  if (typeof AbortSignal === "undefined" || typeof AbortSignal.timeout !== "function") {
    return signal;
  }
  const timeoutSignal = AbortSignal.timeout(REQUEST_TIMEOUT_MS);
  if (!signal) return timeoutSignal;
  if (typeof AbortSignal.any === "function") {
    return AbortSignal.any([signal, timeoutSignal]);
  }
  return signal;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
    signal: withTimeout(init?.signal ?? undefined),
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      detail = data?.detail || detail;
    } catch {
      // тело может быть пустым — оставляем статус
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

// ---------- Публичные методы ----------
export const api = {
  /** Динамический расчёт стоимости и времени. */
  getQuote(payload: QuoteRequest, signal?: AbortSignal) {
    return request<QuoteResponse>("/pricing/quote", {
      method: "POST",
      body: JSON.stringify(payload),
      signal,
    });
  },

  /** Каталог города: услуги и доп.услуги с ценами (для квиза). */
  getCityCatalog(citySlug: string, signal?: AbortSignal) {
    return request<CityCatalog>(`/cities/${encodeURIComponent(citySlug)}/services`, { signal });
  },

  /** Приём лида (обратный звонок / заказ из квиза). */
  createLead(payload: LeadRequest) {
    return request<LeadResponse>("/leads", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /** Свободные слоты мастеров. */
  getAvailability(citySlug: string = DEFAULT_CITY_SLUG, date?: string) {
    const params = new URLSearchParams({ city_slug: citySlug });
    if (date) params.set("date", date);
    return request<Slot[]>(`/booking/availability?${params.toString()}`);
  },

  /** Оформление бронирования. */
  createBooking(payload: BookingRequest) {
    return request<BookingResponse>("/booking/bookings", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /** Опубликованные отзывы (для слайдера на сайте). */
  getReviews(citySlug?: string, limit = 30, signal?: AbortSignal) {
    const params = new URLSearchParams();
    if (citySlug) params.set("city_slug", citySlug);
    params.set("limit", String(limit));
    return request<Review[]>(`/reviews?${params.toString()}`, { signal });
  },

  /** Кейсы «До/После» с карточками заказов. */
  getBeforeAfter(citySlug?: string, signal?: AbortSignal) {
    const params = new URLSearchParams();
    if (citySlug) params.set("city_slug", citySlug);
    const query = params.toString();
    return request<BeforeAfterCase[]>(`/before-after${query ? `?${query}` : ""}`, { signal });
  },
};

export { ApiError, API_BASE };
