// Глобальный контекст аутентификации (OTP-вход).
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api } from "@/api/client";
import { tokenStorage } from "@/api/storage";
import type { UserOut } from "@/api/types";

interface AuthState {
  user: UserOut | null;
  isLoading: boolean;
  requestCode: (phone: string) => Promise<{ debugCode?: string | null }>;
  verifyCode: (phone: string, code: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // При старте — пробуем восстановить сессию по сохранённому токену.
  // Любой сбой (хранилище, сеть) не должен оставлять приложение на сплэше.
  useEffect(() => {
    (async () => {
      try {
        const access = await tokenStorage.getAccess();
        if (access) {
          try {
            setUser(await api.me());
          } catch {
            await tokenStorage.clear();
          }
        }
      } catch (error) {
        console.warn("Не удалось восстановить сессию", error);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      isLoading,
      async requestCode(phone: string) {
        const res = await api.requestOtp(phone, "client");
        return { debugCode: res.debug_code };
      },
      async verifyCode(phone: string, code: string) {
        const pair = await api.verifyOtp(phone, code, "client");
        await tokenStorage.save(pair.access_token, pair.refresh_token);
        setUser(await api.me());
      },
      async signOut() {
        const refresh = await tokenStorage.getRefresh();
        if (refresh) {
          try {
            await api.logout(refresh);
          } catch {
            // даже если сервер недоступен — чистим локально
          }
        }
        await tokenStorage.clear();
        setUser(null);
      },
    }),
    [user, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth должен вызываться внутри <AuthProvider>");
  return ctx;
}

