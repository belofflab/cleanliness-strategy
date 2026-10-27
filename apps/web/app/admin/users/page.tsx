"use client";

import { useCallback, useState } from "react";
import { adminApi, AdminApiError, AdminUser, ROLE_LABELS } from "@/lib/admin";
import { useAdminData } from "@/lib/use-admin-data";

const ROLES = ["client", "master", "manager", "admin"];
const PRIVILEGED = new Set(["manager", "admin"]);

export default function UsersPage() {
  const [roleFilter, setRoleFilter] = useState("all");
  const loadUsers = useCallback(() => adminApi.listUsers(roleFilter), [roleFilter]);
  const { data, error, loading, reload, setError } = useAdminData(loadUsers);
  const users = data?.items ?? [];

  const [form, setForm] = useState({ phone: "", role: "manager", full_name: "", password: "" });

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await adminApi.createUser({
        phone: form.phone.trim(),
        role: form.role,
        full_name: form.full_name.trim() || undefined,
        password: PRIVILEGED.has(form.role) ? form.password : undefined,
      });
      setForm({ phone: "", role: "manager", full_name: "", password: "" });
      reload();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось создать пользователя");
    }
  };

  const toggleActive = async (u: AdminUser) => {
    try {
      await adminApi.updateUser(u.id, { is_active: !u.is_active });
      reload();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Ошибка");
    }
  };

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-2xl font-semibold text-slate-900">Пользователи</h1>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm outline-none focus:border-brand"
        >
          <option value="all">Все роли</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABELS[r]}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <form
        onSubmit={create}
        className="mb-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-5"
      >
        <input
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
          placeholder="Телефон"
          required
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <input
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          placeholder="ФИО"
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <select
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABELS[r]}
            </option>
          ))}
        </select>
        <input
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          placeholder={PRIVILEGED.has(form.role) ? "Пароль (обязателен)" : "Пароль не нужен"}
          disabled={!PRIVILEGED.has(form.role)}
          required={PRIVILEGED.has(form.role)}
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand disabled:bg-slate-50 disabled:text-muted"
        />
        <button
          type="submit"
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Создать
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
                <th className="px-4 py-3">Роль</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium text-slate-900">{u.full_name || "—"}</td>
                  <td className="px-4 py-3 text-slate-600">{u.phone}</td>
                  <td className="px-4 py-3 text-slate-600">{ROLE_LABELS[u.role] || u.role}</td>
                  <td className="px-4 py-3">
                    {u.is_active ? (
                      <span className="text-emerald-700">активен</span>
                    ) : (
                      <span className="text-muted">заблокирован</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => toggleActive(u)}
                      className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                    >
                      {u.is_active ? "Заблокировать" : "Разблокировать"}
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-muted">
                    Нет пользователей
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
