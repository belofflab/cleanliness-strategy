"use client";

import { useCallback, useState } from "react";
import { useAdmin } from "@/lib/admin-context";
import { adminApi, AdminApiError, Master } from "@/lib/admin";
import { useAdminData } from "@/lib/use-admin-data";
import { CITY_PROFILES, CITY_SLUGS } from "@/lib/city";

export default function MastersPage() {
  const { city } = useAdmin();
  const loadMasters = useCallback(() => adminApi.listMasters(city), [city]);
  const { data, error, loading, reload, setError } = useAdminData(loadMasters);
  const masters = data ?? [];

  const [form, setForm] = useState<{ city_slug: string; full_name: string; phone: string }>({
    city_slug: CITY_SLUGS[0],
    full_name: "",
    phone: "",
  });

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await adminApi.createMaster({
        city_slug: form.city_slug,
        full_name: form.full_name.trim(),
        phone: form.phone.trim() || undefined,
      });
      setForm({ ...form, full_name: "", phone: "" });
      reload();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось создать клинера");
    }
  };

  const toggleActive = async (m: Master) => {
    try {
      await adminApi.updateMaster(m.id, { is_active: !m.is_active });
      reload();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Ошибка");
    }
  };

  return (
    <div>
      <h1 className="mb-4 font-display text-2xl font-semibold text-slate-900">Клинеры</h1>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <form
        onSubmit={create}
        className="mb-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-4"
      >
        <select
          value={form.city_slug}
          onChange={(e) => setForm({ ...form, city_slug: e.target.value })}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        >
          {CITY_SLUGS.map((slug) => (
            <option key={slug} value={slug}>
              {CITY_PROFILES[slug].name}
            </option>
          ))}
        </select>
        <input
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          placeholder="ФИО клинера"
          required
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <input
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
          placeholder="Телефон (для входа в моб. приложение)"
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <button
          type="submit"
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Добавить
        </button>
      </form>

      {loading ? (
        <p className="text-muted">Загрузка…</p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-3">Имя</th>
                <th className="px-4 py-3">Телефон</th>
                <th className="px-4 py-3">Рейтинг</th>
                <th className="px-4 py-3">Учётка</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {masters.map((m) => (
                <tr key={m.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium text-slate-900">{m.full_name}</td>
                  <td className="px-4 py-3 text-slate-600">{m.phone || "—"}</td>
                  <td className="px-4 py-3 text-slate-600">{m.rating.toFixed(2)}</td>
                  <td className="px-4 py-3">
                    {m.has_account ? (
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                        привязана
                      </span>
                    ) : (
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-muted">
                        нет
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {m.is_active ? (
                      <span className="text-emerald-700">активен</span>
                    ) : (
                      <span className="text-muted">скрыт</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => toggleActive(m)}
                      className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                    >
                      {m.is_active ? "Скрыть" : "Включить"}
                    </button>
                  </td>
                </tr>
              ))}
              {masters.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-muted">
                    Нет клинеров
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
