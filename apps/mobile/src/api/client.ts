// HTTP-клиент backend «Точка Чистоты».
// База — из EXPO_PUBLIC_API_URL (бандлится в приложение, всегда с /api/v1 на конце).
// Поддерживает прозрачную ротацию access-токена через refresh при 401.

import { tokenStorage } from "./storage";
import type {
  BookingRequest,
  BookingResponse,
  Master,
  OtpRequestResult,
  QuoteRequest,
  QuoteResponse,
  Review,
  Slot,
  TokenPair,
  UserOut,
} from "./types";

const API_BASE = (
  process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");

// Город по умолчанию — как на сайте и бэкенде (DEFAULT_CITY_SLUG): бизнес Уфа-first.
export const DEFAULT_CITY = process.env.EXPO_PUBLIC_DEFAULT_CITY || "ufa";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions extends RequestInit {
  auth?: boolean; // приложить Bearer access-токен
  _retry?: boolean; // внутренний флаг — защита от бесконечной ротации
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = await tokenStorage.getRefresh();
  if (!refresh) return false;

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) {
    await tokenStorage.clear();
    return false;
  }
  const pair = (await res.json()) as TokenPair;
  await tokenStorage.save(pair.access_token, pair.refresh_token);
  return true;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth, _retry, headers, ...init } = options;

  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...((headers as Record<string, string>) || {}),
  };

  if (auth) {
    const access = await tokenStorage.getAccess();
    if (access) finalHeaders.Authorization = `Bearer ${access}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers: finalHeaders });

  // Прозрачная ротация токена: один раз пробуем refresh и повтор запроса.
  if (res.status === 401 && auth && !_retry) {
    const ok = await refreshAccessToken();
    if (ok) return request<T>(path, { ...options, _retry: true });
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      detail = data?.detail || detail;
    } catch {
      // тело может быть пустым
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  base: API_BASE,

  // ---- Auth (OTP) ----
  requestOtp(phone: string, role = "client") {
    return request<OtpRequestResult>("/auth/otp/request", {
      method: "POST",
      body: JSON.stringify({ phone, role }),
    });
  },
  verifyOtp(phone: string, code: string, role = "client") {
    return request<TokenPair>("/auth/otp/verify", {
      method: "POST",
      body: JSON.stringify({ phone, code, role }),
    });
  },
  logout(refresh_token: string) {
    return request<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    });
  },
  me() {
    return request<UserOut>("/auth/me", { auth: true });
  },

  // ---- Booking ----
  getMasters(city_slug = DEFAULT_CITY) {
    return request<Master[]>(`/booking/masters?city_slug=${encodeURIComponent(city_slug)}`);
  },
  getAvailability(city_slug = DEFAULT_CITY, date?: string) {
    const params = new URLSearchParams({ city_slug });
    if (date) params.set("date", date);
    return request<Slot[]>(`/booking/availability?${params.toString()}`);
  },
  createBooking(payload: BookingRequest) {
    return request<BookingResponse>("/booking/bookings", {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    });
  },

  // ---- Pricing ----
  getQuote(payload: QuoteRequest) {
    return request<QuoteResponse>("/pricing/quote", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // ---- Reviews ----
  getReviews(city_slug?: string, limit = 30) {
    const params = new URLSearchParams();
    if (city_slug) params.set("city_slug", city_slug);
    params.set("limit", String(limit));
    return request<Review[]>(`/reviews?${params.toString()}`);
  },
};

