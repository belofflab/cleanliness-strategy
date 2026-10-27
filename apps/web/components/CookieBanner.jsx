"use client";

import { useState } from "react";
import Link from "next/link";
import cookieConsent from "@/lib/cookie-consent";

// Компактный cookie-баннер (ТЗ п.12): узкая плашка внизу, не перекрывает
// контент и CTA первого экрана. Выбор сохраняется в localStorage.
export default function CookieBanner() {
  const [visible, setVisible] = useState(() => !cookieConsent.get());

  const handleAccept = () => {
    cookieConsent.accept();
    setVisible(false);
  };

  const handleReject = () => {
    cookieConsent.reject();
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 px-3 pb-3 sm:px-6">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-3 rounded-2xl border border-white/50 bg-surface p-4 shadow-2xl shadow-slate-900/15 backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs leading-5 text-slate-700 sm:max-w-md">
          Используем cookie для работы сайта и аналитики.{" "}
          <Link href="/privacy" className="font-semibold text-brand-deep transition hover:text-brand">
            Подробнее
          </Link>
        </p>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={handleReject}
            className="flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 sm:flex-none"
          >
            Только необходимые
          </button>
          <button
            type="button"
            onClick={handleAccept}
            className="flex-1 rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 sm:flex-none"
          >
            Принять
          </button>
        </div>
      </div>
    </div>
  );
}
