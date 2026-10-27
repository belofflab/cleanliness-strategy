// Отправка целей и событий в Яндекс Метрику.
//
// Счётчик один на сайт и инициализируется скриптом в layout.tsx
// (components/YandexMetrika.jsx) — здесь его НЕ инициализируем, иначе
// двойной init искажает визиты и показатель отказов.
//
// Цели (Lead / Call / FormSubmit / ThankYou) должны срабатывать у всех
// посетителей: на них настраивается оптимизация рекламных кампаний (ТЗ п.10),
// поэтому они не зависят от cookie-согласия — сам счётчик подключён на уровне
// layout безусловно.
const YANDEX_COUNTER_ID =
  Number(process.env.NEXT_PUBLIC_YANDEX_METRICA_ID) || 109824753;

export function trackYandexGoal(goalName, payload = {}) {
  if (typeof window === "undefined") return;
  if (typeof goalName !== "string" || !goalName.trim()) return;
  if (typeof window.ym !== "function") return;

  window.ym(YANDEX_COUNTER_ID, "reachGoal", goalName, payload);
}

export function trackLeadGoal(payload = {}) {
  trackYandexGoal("Lead", payload);
}

export function trackCallGoal(payload = {}) {
  trackYandexGoal("Call", payload);
}

export function trackFormSubmitGoal(payload = {}) {
  trackYandexGoal("FormSubmit", payload);
}

export function trackEvent(eventName, payload = {}) {
  if (typeof window === "undefined") return;

  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ event: eventName, ...payload });

  if (typeof window.gtag === "function") {
    window.gtag("event", eventName, payload);
  }

  if (eventName === "callback_submit_success" || eventName === "quiz_submit_success") {
    trackLeadGoal(payload);
    trackFormSubmitGoal(payload);
  }

  if (eventName === "phone_click") {
    trackCallGoal(payload);
  }

  // Просмотр страницы «Спасибо» — цель для оптимизации рекламных кампаний (ТЗ п.10).
  if (eventName === "thankyou_view") {
    trackYandexGoal("ThankYou", payload);
  }
}
