// Клиент админ-CRM API «Точка Чистоты».
// Токен (staff) хранится в localStorage; каждый запрос идёт с Bearer.
// База — общая с публичным API (NEXT_PUBLIC_API_URL → /api/v1).

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000/api/v1";

const TOKEN_KEY = "tc_admin_access";
const REFRESH_KEY = "tc_admin_refresh";

// ---------- Типы ----------
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Order {
  id: string;
  status: string;
  city: string | null;
  city_slug: string | null;
  service: string | null;
  service_type: string | null;
  customer_name: string | null;
  customer_phone: string | null;
  master_id: string | null;
  master_name: string | null;
  rooms: number;
  bathrooms: number;
  total_price: number;
  est_minutes: number;
  scheduled_at: string | null;
  created_at: string;
}

export type OrderBoard = Record<string, Order[]>;

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminUser {
  id: string;
  phone: string;
  email: string | null;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Master {
  id: string;
  city_id: string;
  full_name: string;
  phone: string | null;
  rating: number;
  photo_url: string | null;
  is_active: boolean;
  has_account: boolean;
}

export interface FinanceEntry {
  id: string;
  kind: string;
  amount: number;
  category: string;
  city_id: string | null;
  order_id: string | null;
  note: string | null;
  occurred_at: string;
  created_at: string;
}

export interface FinanceSummary {
  income: number;
  expense: number;
  profit: number;
}

export interface Lead {
  id: string;
  name: string;
  phone: string;
  source: string;
  city: string | null;
  city_slug: string | null;
  status: string;
  context: string | null;
  // Сквозная аналитика: атрибуция и сегментация.
  service_type: string | null;
  price: number | null;
  utm: Record<string, string> | null;
  yclid: string | null;
  gclid: string | null;
  ym_uid: string | null;
  // Собственная CRM.
  assignee_id: string | null;
  assignee_name: string | null;
  manager_note: string | null;
  created_at: string;
}

export interface LeadUpdatePayload {
  status?: string;
  manager_note?: string;
  assignee_id?: string | null;
}

export interface LeadConvertPayload {
  service_type: string;
  rooms: number;
  bathrooms: number;
  addon_codes?: string[];
}

export interface LeadFilters {
  status?: string;
  source?: string;
  utm_source?: string;
  utm_campaign?: string;
}

export interface LeadSummaryItem {
  value: string;
  count: number;
}

export interface LeadSummary {
  by_source: LeadSummaryItem[];
  by_utm_source: LeadSummaryItem[];
  by_campaign: LeadSummaryItem[];
  by_status: LeadSummaryItem[];
  by_service: LeadSummaryItem[];
}

// Воронка собственной CRM.
export const LEAD_STATUS_LABELS: Record<string, string> = {
  new: "Новый",
  in_progress: "В работе",
  converted: "Заказ создан",
  rejected: "Отказ",
};

export const LEAD_STATUS_ORDER = ["new", "in_progress", "converted", "rejected"] as const;

export const LEAD_SOURCE_LABELS: Record<string, string> = {
  quiz: "Квиз",
  callback: "Обратный звонок",
  call: "Звонок (Calltracking)",
  hero: "Сайт",
  footer: "Сайт",
  cta: "Сайт",
  header: "Сайт",
  booking: "Букинг",
  unknown: "Не определён",
};

export const ORDER_STATUSES = [
  "new",
  "assigned",
  "in_progress",
  "done",
  "cancelled",
] as const;

export const STATUS_LABELS: Record<string, string> = {
  new: "Новые",
  assigned: "Назначены",
  in_progress: "В работе",
  done: "Завершены",
  cancelled: "Отменены",
};

export const ROLE_LABELS: Record<string, string> = {
  client: "Клиент",
  master: "Клинер",
  manager: "Менеджер",
  admin: "Администратор",
};

// ---------- Хранилище токенов ----------
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setTokens(pair: TokenPair) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, pair.access_token);
  window.localStorage.setItem(REFRESH_KEY, pair.refresh_token);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

// ---------- Ошибки ----------
export class AdminApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
  }
}

// Эндпоинты, где 401 означает неверные учётные данные, а не истёкший access-токен.
const NO_REFRESH_PATHS = ["/auth/login", "/auth/refresh", "/auth/logout"];

// Одна ротация на все параллельные 401: запросы ждут общий refresh, а не плодят свои.
let refreshing: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!response.ok) return false;
    setTokens((await response.json()) as TokenPair);
    return true;
  } catch {
    return false;
  }
}

async function readDetail(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json();
    return typeof data?.detail === "string" && data.detail ? data.detail : fallback;
  } catch {
    return fallback; // пустое тело — оставляем дефолт
  }
}

async function request<T>(path: string, init?: RequestInit, allowRefresh = true): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });

  if (response.status === 401) {
    // Access-токен живёт 15 минут: прозрачно обновляем пару по refresh и
    // повторяем запрос один раз. Логин/refresh/logout не ротируем: там 401 —
    // «Неверный логин или пароль» (detail бэкенда), а не истёкшая сессия.
    const isCredentialPath = NO_REFRESH_PATHS.some((prefix) => path.startsWith(prefix));
    if (allowRefresh && !isCredentialPath && getRefreshToken()) {
      refreshing ??= refreshTokens().finally(() => {
        refreshing = null;
      });
      if (await refreshing) return request<T>(path, init, false);
    }
    const detail = await readDetail(response, "Сессия истекла, войдите снова");
    if (!isCredentialPath) clearTokens();
    throw new AdminApiError(detail, 401);
  }
  if (!response.ok) {
    throw new AdminApiError(await readDetail(response, `HTTP ${response.status}`), response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function cityQuery(citySlug?: string | null): string {
  return citySlug && citySlug !== "all" ? `?city_slug=${encodeURIComponent(citySlug)}` : "";
}

// ---------- API ----------
export const adminApi = {
  async login(login: string, password: string): Promise<TokenPair> {
    const pair = await request<TokenPair>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ login, password }),
    });
    setTokens(pair);
    return pair;
  },

  me() {
    return request<{ id: string; phone: string; role: string; full_name: string | null }>(
      "/auth/me"
    );
  },

  /** Выход: отзыв refresh-токенов устройства на сервере + очистка локальной сессии. */
  async logout(): Promise<void> {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await request<void>(
          "/auth/logout",
          { method: "POST", body: JSON.stringify({ refresh_token: refresh }) },
          false,
        );
      }
    } catch {
      // сервер недоступен — локальную сессию всё равно чистим
    } finally {
      clearTokens();
    }
  },

  // Лиды: сайт (квиз/обратный звонок) + звонки Calltracking.
  // Фильтры — сепарация по статусу, источнику и рекламной атрибуции.
  listLeads(citySlug?: string | null, filters?: LeadFilters) {
    const params = new URLSearchParams();
    if (citySlug && citySlug !== "all") params.set("city_slug", citySlug);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.source) params.set("source", filters.source);
    if (filters?.utm_source) params.set("utm_source", filters.utm_source);
    if (filters?.utm_campaign) params.set("utm_campaign", filters.utm_campaign);
    const query = params.toString();
    return request<Page<Lead>>(`/admin/leads${query ? `?${query}` : ""}`);
  },
  leadsSummary(citySlug?: string | null) {
    return request<LeadSummary>(`/admin/leads/summary${cityQuery(citySlug)}`);
  },
  updateLead(leadId: string, payload: LeadUpdatePayload) {
    return request<Lead>(`/admin/leads/${leadId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  convertLead(leadId: string, payload: LeadConvertPayload) {
    return request<Order>(`/admin/leads/${leadId}/convert`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Заказы
  ordersBoard(citySlug?: string | null) {
    return request<OrderBoard>(`/admin/orders/board${cityQuery(citySlug)}`);
  },
  setOrderStatus(orderId: string, status: string) {
    return request<Order>(`/admin/orders/${orderId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },
  assignMaster(orderId: string, masterId: string | null) {
    return request<Order>(`/admin/orders/${orderId}/assign`, {
      method: "PATCH",
      body: JSON.stringify({ master_id: masterId }),
    });
  },

  // Пользователи
  listUsers(role?: string) {
    const q = role && role !== "all" ? `?role=${encodeURIComponent(role)}` : "";
    return request<Page<AdminUser>>(`/admin/users${q}`);
  },
  createUser(payload: {
    phone: string;
    role: string;
    full_name?: string;
    email?: string;
    password?: string;
  }) {
    return request<AdminUser>("/admin/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateUser(id: string, payload: Partial<{ role: string; is_active: boolean; full_name: string }>) {
    return request<AdminUser>(`/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  // Клинеры
  listMasters(citySlug?: string | null) {
    return request<Master[]>(`/admin/masters${cityQuery(citySlug)}`);
  },
  createMaster(payload: { city_slug: string; full_name: string; phone?: string }) {
    return request<Master>("/admin/masters", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateMaster(id: string, payload: Partial<{ full_name: string; phone: string; is_active: boolean }>) {
    return request<Master>(`/admin/masters/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  // Финансы
  listFinance(citySlug?: string | null) {
    return request<FinanceEntry[]>(`/admin/finance${cityQuery(citySlug)}`);
  },
  financeSummary(citySlug?: string | null) {
    return request<FinanceSummary>(`/admin/finance/summary${cityQuery(citySlug)}`);
  },
  createFinance(payload: {
    kind: string;
    amount: number;
    category?: string;
    city_slug?: string;
    note?: string;
  }) {
    return request<FinanceEntry>("/admin/finance", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
