"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { adminApi, clearTokens, getRefreshToken, getToken } from "@/lib/admin";
import { CITY_PROFILES, CITY_SLUGS } from "@/lib/city";

type Me = { id: string; phone: string; role: string; full_name: string | null };

interface AdminContextValue {
  authed: boolean;
  ready: boolean; // первичная проверка токена завершена
  me: Me | null;
  city: string; // "all" | citySlug
  setCity: (c: string) => void;
  cityOptions: { value: string; label: string }[];
  login: (login: string, password: string) => Promise<void>;
  logout: () => void;
}

const AdminContext = createContext<AdminContextValue | null>(null);

export function useAdmin(): AdminContextValue {
  const ctx = useContext(AdminContext);
  if (!ctx) throw new Error("useAdmin вне AdminProvider");
  return ctx;
}

const CITY_OPTIONS = [
  { value: "all", label: "Все города" },
  ...CITY_SLUGS.map((slug) => ({ value: slug, label: CITY_PROFILES[slug].name })),
];

export function AdminProvider({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState(false);
  const [ready, setReady] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [city, setCity] = useState("all");

  // Первичная проверка: есть access- или refresh-токен → валидируем через /auth/me
  // (истёкший access прозрачно обновляется по refresh в lib/admin.ts).
  useEffect(() => {
    let active = true;
    (async () => {
      if (!getToken() && !getRefreshToken()) {
        setReady(true);
        return;
      }
      try {
        const profile = await adminApi.me();
        if (active) {
          setMe(profile);
          setAuthed(true);
        }
      } catch {
        clearTokens();
      } finally {
        if (active) setReady(true);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const login = async (loginValue: string, password: string) => {
    await adminApi.login(loginValue, password);
    const profile = await adminApi.me();
    setMe(profile);
    setAuthed(true);
  };

  const logout = () => {
    // Отзыв refresh-токенов на сервере — фоном; локальную сессию чистим сразу.
    void adminApi.logout();
    clearTokens();
    setMe(null);
    setAuthed(false);
  };

  return (
    <AdminContext.Provider
      value={{ authed, ready, me, city, setCity, cityOptions: CITY_OPTIONS, login, logout }}
    >
      {children}
    </AdminContext.Provider>
  );
}
