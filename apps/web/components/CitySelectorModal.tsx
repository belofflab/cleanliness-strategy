"use client";

import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, MapPin } from "lucide-react";
import {
  ACTIVE_CITY_SLUGS,
  CITY_PROFILES,
  type CitySlug,
} from "@/lib/city";

type CitySelectorModalProps = {
  currentCitySlug: CitySlug;
  onSelectCity: (citySlug: CitySlug) => void;
};

export default function CitySelectorModal({
  currentCitySlug,
  onSelectCity,
}: CitySelectorModalProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const currentCity = CITY_PROFILES[currentCitySlug];

  useEffect(() => {
    if (!open) return;

    const handleOutsidePointer = (event: MouseEvent) => {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    window.addEventListener("mousedown", handleOutsidePointer);
    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("mousedown", handleOutsidePointer);
      window.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  // Один активный город — выбор не нужен: показываем просто бейдж города.
  if (ACTIVE_CITY_SLUGS.length < 2) {
    return (
      <span className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm">
        <MapPin size={15} className="text-brand-deep" />
        {currentCity.name}
      </span>
    );
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50"
      >
        <MapPin size={15} className="text-brand-deep" />
        <span>{currentCity.name}</span>
        <ChevronDown size={14} className={`text-slate-500 transition ${open ? "rotate-180" : ""}`} />
      </button>

      {open ? (
        <section
          role="listbox"
          aria-label="Выбор города"
          className="fixed inset-x-3 top-[4.75rem] z-50 max-h-[min(70vh,32rem)] overflow-y-auto rounded-3xl border border-slate-200/80 bg-white/95 p-3 shadow-2xl shadow-slate-900/15 backdrop-blur-lg sm:absolute sm:inset-x-auto sm:right-0 sm:top-[calc(100%+10px)] sm:max-h-none sm:w-[min(22rem,calc(100vw-2rem))] sm:overflow-visible"
        >
          <p className="px-2 pb-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
            Выберите город
          </p>

          <div className="space-y-2">
            {ACTIVE_CITY_SLUGS.map((citySlug) => {
              const city = CITY_PROFILES[citySlug];
              const isActive = citySlug === currentCitySlug;

              return (
                <button
                  key={citySlug}
                  type="button"
                  onClick={() => {
                    onSelectCity(citySlug);
                    setOpen(false);
                  }}
                  className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                    isActive
                      ? "border-brand-deep/20 bg-gradient-to-r from-slate-900 to-brand-deep text-white shadow-lg shadow-slate-900/20"
                      : "border-slate-200 bg-white text-slate-800 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-medium">{city.name}</div>
                    {isActive ? <Check size={14} className="text-white" /> : null}
                  </div>
                  <div className={`mt-0.5 text-xs ${isActive ? "text-slate-100" : "text-slate-500"}`}>
                    {city.phone}
                  </div>
                </button>
              );
            })}
          </div>

          <p className="pt-3 px-2 text-xs text-muted">
            Город влияет на телефон, цены и доступность услуг.
          </p>
        </section>
      ) : null}
    </div>
  );
}
