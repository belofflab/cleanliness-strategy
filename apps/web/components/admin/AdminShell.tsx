"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAdmin } from "@/lib/admin-context";
import { ROLE_LABELS } from "@/lib/admin";

const NAV = [
  { href: "/admin", label: "Заказы" },
  { href: "/admin/leads", label: "Лиды" },
  { href: "/admin/masters", label: "Клинеры" },
  { href: "/admin/users", label: "Пользователи" },
  { href: "/admin/finance", label: "Финансы" },
];

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const { me, city, setCity, cityOptions, logout } = useAdmin();
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-surface-strong/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <span className="font-display text-lg font-semibold text-slate-900">
            Точка Чистоты · CRM
          </span>
          <nav className="flex items-center gap-1 text-sm">
            {NAV.map((item) => {
              const active =
                item.href === "/admin"
                  ? pathname === "/admin"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-lg px-3 py-1.5 font-medium transition ${
                    active
                      ? "bg-slate-900 text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            {/* Региональный фильтр — общий для всех разделов. */}
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 outline-none focus:border-brand"
              aria-label="Фильтр по городу"
            >
              {cityOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <span className="hidden text-sm text-muted sm:inline">
              {me?.full_name || me?.phone} · {ROLE_LABELS[me?.role || ""] || me?.role}
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            >
              Выйти
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
