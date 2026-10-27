"use client";

import { useState } from "react";
import { useAdmin } from "@/lib/admin-context";
import { AdminApiError } from "@/lib/admin";

export default function AdminLogin() {
  const { login } = useAdmin();
  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(loginValue.trim(), password);
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось войти");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-3xl border border-white/40 bg-surface-strong p-8 shadow-xl shadow-slate-900/5"
      >
        <h1 className="font-display text-2xl font-semibold text-slate-900">Админ-панель</h1>
        <p className="mt-1 text-sm text-muted">Точка Чистоты — вход для сотрудников</p>

        <label className="mt-6 block text-sm font-medium text-slate-700">
          Телефон или email
          <input
            type="text"
            autoComplete="username"
            value={loginValue}
            onChange={(e) => setLoginValue(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900 outline-none focus:border-brand"
            placeholder="+7 (999) 000-00-00"
            required
          />
        </label>

        <label className="mt-4 block text-sm font-medium text-slate-700">
          Пароль
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900 outline-none focus:border-brand"
            required
          />
        </label>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full rounded-xl bg-slate-900 px-4 py-2.5 font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
        >
          {loading ? "Вход…" : "Войти"}
        </button>
      </form>
    </div>
  );
}
