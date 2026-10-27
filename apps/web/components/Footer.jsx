"use client";

import Link from "next/link";
import {
  Banknote,
  Building2,
  Clock3,
  CreditCard,
  ExternalLink,
  Landmark,
  Mail,
  MapPin,
  MessageCircleMore,
  Navigation,
  Phone,
  Send,
} from "lucide-react";
import { trackEvent } from "@/lib/analytics";
import Logo from "@/components/Logo";

function toPhoneLink(phone) {
  const normalized = phone.replace(/[^\d+]/g, "");
  return normalized.startsWith("+") ? normalized : `+${normalized}`;
}

// Способы оплаты (ТЗ п.9.5). Оплата — после приёмки уборки.
const PAYMENT_METHODS = [
  { icon: Banknote, label: "Наличные" },
  { icon: CreditCard, label: "Карта / перевод по СБП" },
  { icon: Landmark, label: "Счёт для юрлиц" },
];

export default function Footer({ onOpenCallback, cityProfile }) {
  const city = cityProfile;
  const cityPhoneLink = toPhoneLink(city.phone);

  return (
    <footer id="contacts" className="px-4 pb-8 pt-16 sm:px-6 lg:px-10">
      <div className="mx-auto w-full max-w-6xl rounded-4xl border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
        <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Контакты {city.namePrepositional}
        </h2>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          {/* Левая колонка: связь и условия выезда */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <Logo size={30} textClassName="text-lg text-slate-950" />
              <div className="mt-4 space-y-2.5 text-sm text-slate-800">
                <p className="flex items-start gap-2.5">
                  <MapPin size={16} className="mt-0.5 shrink-0 text-brand-deep" />
                  {city.locality}, {city.primaryBranchAddress}
                </p>
                <a
                  className="flex items-center gap-2.5 font-semibold transition hover:text-brand-deep"
                  href={`tel:${cityPhoneLink}`}
                  onClick={() => trackEvent("phone_click", { place: "footer", phone: cityPhoneLink })}
                >
                  <Phone size={16} className="shrink-0 text-brand-deep" />
                  {city.phone}
                </a>
                <a
                  className="flex items-center gap-2.5 transition hover:text-brand-deep"
                  href={`mailto:${city.email}`}
                  onClick={() => trackEvent("email_click", { place: "footer" })}
                >
                  <Mail size={16} className="shrink-0 text-brand-deep" />
                  {city.email}
                </a>
                <p className="flex items-center gap-2.5">
                  <Clock3 size={16} className="shrink-0 text-brand-deep" />
                  {city.workingHours}
                </p>
              </div>

              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                <a
                  href="https://t.me/pointclean"
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => trackEvent("messenger_click", { messenger: "telegram", place: "footer" })}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-sky-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-600"
                >
                  <Send size={15} /> Telegram
                </a>
                <a
                  href="https://max.ru/u/f9LHodD0cOJ-1c8HG-4TAxVQZJip_UiDUg0UWG0JD0mSYbnaQFc9UpKhxs0"
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => trackEvent("messenger_click", { messenger: "max", place: "footer" })}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-600"
                >
                  <MessageCircleMore size={15} /> Max
                </a>
                <button
                  type="button"
                  onClick={() => onOpenCallback("Запрос из блока контактов")}
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 sm:col-span-2"
                >
                  <Phone size={15} /> Обратный звонок
                </button>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Районы выезда</p>
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {city.districts.map((district) => (
                  <li
                    key={district}
                    className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700"
                  >
                    {district}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs leading-5 text-muted">{city.outOfCityNote}</p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Способы оплаты</p>
              <ul className="mt-3 space-y-2 text-sm text-slate-800">
                {PAYMENT_METHODS.map((method) => {
                  const Icon = method.icon;
                  return (
                    <li key={method.label} className="flex items-center gap-2.5">
                      <Icon size={15} className="shrink-0 text-brand-deep" />
                      {method.label}
                    </li>
                  );
                })}
              </ul>
              <p className="mt-3 text-xs text-muted">Оплата после приёмки уборки. Скрытых доплат нет.</p>
            </div>
          </div>

          {/* Правая колонка: карта, профили, реквизиты */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="overflow-hidden rounded-xl border border-slate-200">
                {/* Встроенная Яндекс Карта: lazy — не тормозит первую загрузку. */}
                <iframe
                  src={city.mapEmbedSrc}
                  title={`Точка Чистоты на карте — ${city.locality}`}
                  className="h-56 w-full"
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              </div>
              <a
                href={city.routeUrl}
                target="_blank"
                rel="noreferrer"
                onClick={() => trackEvent("route_click", { city_slug: city.slug })}
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                <Navigation size={15} />
                Построить маршрут
              </a>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Мы на площадках</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <a
                  href={city.yandexBusinessUrl}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => trackEvent("platform_click", { platform: "yandex", place: "footer" })}
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
                >
                  Яндекс Бизнес <ExternalLink size={13} />
                </a>
                <a
                  href={city.twoGisUrl}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => trackEvent("platform_click", { platform: "2gis", place: "footer" })}
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
                >
                  2ГИС <ExternalLink size={13} />
                </a>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Реквизиты</p>
              <p className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-slate-800">
                <Building2 size={15} /> ООО «ОМ»
              </p>
              <p className="mt-1 text-xs text-muted">ИНН 0273955232</p>
              <p className="mt-1 text-xs text-muted">ОГРН 1260200001401</p>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Правовые документы</p>
            <p className="mt-2 text-sm font-medium text-slate-700">Текущий город: {city.name}</p>
            <div className="mt-3 flex flex-wrap gap-3">
              <Link href="/oferta" className="text-sm font-semibold text-slate-700 transition hover:text-brand-deep">
                Договор оферты
              </Link>
              <Link href="/privacy" className="text-sm font-semibold text-slate-700 transition hover:text-brand-deep">
                Политика конфиденциальности
              </Link>
            </div>
            <p className="mt-3 text-xs leading-5 text-muted">
              Cookie-файлы и аналитика используются только после согласия пользователя.
            </p>
          </div>

          <p className="text-sm font-medium text-slate-700">© Blanq Tech | 2026 | Все права защищены</p>
        </div>
      </div>
    </footer>
  );
}
