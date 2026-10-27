// Типы, зеркалирующие DTO backend (services/api/app/schemas).
// Держим в синхроне с FastAPI-схемами.

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserOut {
  id: string;
  phone: string;
  role: string;
  full_name?: string | null;
}

export interface OtpRequestResult {
  sent: boolean;
  debug_code?: string | null;
  message: string;
}

export interface Master {
  id: string;
  full_name: string;
  rating: number;
  photo_url?: string | null;
}

export interface Slot {
  id: string;
  master_id: string;
  master_name: string;
  work_date: string;
  start_time: string;
  end_time: string;
}

export interface QuoteRequest {
  city_slug: string;
  service_type: string; // maintenance | general | post_renovation
  rooms: number;
  bathrooms: number;
  addon_codes: string[];
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
  published_at?: string | null;
}

