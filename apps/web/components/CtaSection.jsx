"use client";

import { ArrowRight } from "lucide-react";

export default function CtaSection({ onOpenCallback }) {
  return (
    <section id="cta" className="px-4 py-16 sm:px-6 lg:px-10">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 rounded-[2rem] border border-sky-200 bg-gradient-to-r from-sky-50 to-cyan-50 p-6 shadow-xl shadow-sky-900/5 md:flex-row md:items-center md:justify-between md:p-10">
        <div>
          <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Готовы к идеальной чистоте?
          </h2>
          <p className="mt-2 text-sm text-slate-700 sm:text-base">
            Оставьте заявку и получите подтверждение стоимости уже во время первого звонка.
          </p>
        </div>
        <button
          type="button"
          onClick={() => onOpenCallback("Финальный CTA-блок")}
          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          Оформить заказ
          <ArrowRight size={16} />
        </button>
      </div>
    </section>
  );
}

