"use client";

import { useCallback, useState } from "react";
import { useAdmin } from "@/lib/admin-context";
import { adminApi, AdminApiError } from "@/lib/admin";
import { useAdminData } from "@/lib/use-admin-data";

function money(value: number) {
  return new Intl.NumberFormat("ru-RU").format(value) + " ₽";
}

export default function FinancePage() {
  const { city } = useAdmin();
  const loadFinance = useCallback(async () => {
    const [summary, entries] = await Promise.all([
      adminApi.financeSummary(city),
      adminApi.listFinance(city),
    ]);
    return { summary, entries };
  }, [city]);
  const { data, error, loading, reload, setError } = useAdminData(loadFinance);
  const summary = data?.summary ?? null;
  const entries = data?.entries ?? [];

  const [form, setForm] = useState({ kind: "income", amount: "", category: "", note: "" });

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const amount = Number(form.amount);
    if (!(amount > 0)) {
      setError("Сумма должна быть больше нуля");
      return;
    }
    try {
      await adminApi.createFinance({
        kind: form.kind,
        amount,
        category: form.category.trim() || undefined,
        city_slug: city !== "all" ? city : undefined,
        note: form.note.trim() || undefined,
      });
      setForm({ kind: "income", amount: "", category: "", note: "" });
      reload();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось добавить проводку");
    }
  };

  return (
    <div>
      <h1 className="mb-4 font-display text-2xl font-semibold text-slate-900">Финансы</h1>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-muted">Доходы</p>
          <p className="mt-1 font-display text-2xl font-semibold text-emerald-600">
            {summary ? money(summary.income) : "—"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-muted">Расходы</p>
          <p className="mt-1 font-display text-2xl font-semibold text-red-600">
            {summary ? money(summary.expense) : "—"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-muted">Прибыль</p>
          <p className="mt-1 font-display text-2xl font-semibold text-slate-900">
            {summary ? money(summary.profit) : "—"}
          </p>
        </div>
      </div>

      <form
        onSubmit={create}
        className="mb-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-5"
      >
        <select
          value={form.kind}
          onChange={(e) => setForm({ ...form, kind: e.target.value })}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        >
          <option value="income">Доход</option>
          <option value="expense">Расход</option>
        </select>
        <input
          type="number"
          min="1"
          step="0.01"
          value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })}
          placeholder="Сумма, ₽"
          required
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <input
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value })}
          placeholder="Категория"
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <input
          value={form.note}
          onChange={(e) => setForm({ ...form, note: e.target.value })}
          placeholder="Комментарий"
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
                <th className="px-4 py-3">Дата</th>
                <th className="px-4 py-3">Тип</th>
                <th className="px-4 py-3">Категория</th>
                <th className="px-4 py-3">Сумма</th>
                <th className="px-4 py-3">Комментарий</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 text-slate-600">
                    {new Date(e.occurred_at).toLocaleDateString("ru-RU")}
                  </td>
                  <td className="px-4 py-3">
                    {e.kind === "income" ? (
                      <span className="text-emerald-700">доход</span>
                    ) : (
                      <span className="text-red-600">расход</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{e.category}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{money(e.amount)}</td>
                  <td className="px-4 py-3 text-slate-600">{e.note || "—"}</td>
                </tr>
              ))}
              {entries.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-muted">
                    Нет проводок
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
