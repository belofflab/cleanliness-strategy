"use client";

import { useSyncExternalStore } from "react";
import Script from "next/script";

// Динамический коллтрекинг Calltracking.ru: скрипт подменяет номера телефонов
// на сайте по источнику трафика посетителя и связывает звонок с сессией,
// client_id Метрики и UTM-метками.
//
// URL счётчика задаётся в NEXT_PUBLIC_CALLTRACKING_SCRIPT_URL (дефолт — в
// .github/workflows/build-and-push.yml). Без переменной компонент не рендерит
// ничего — безопасно для dev/стейджа.
//
// Параметр ?nc= — анти-кэш из официального сниппета CT: значение меняется
// каждые 5 минут, чтобы браузеры регулярно забирали свежий конфиг подмены.
//
// Подмена работает по совпадению текста номера: телефоны городов рендерятся
// из CITY_PROFILES (lib/city.ts) — эти же номера должны быть указаны в
// кабинете CT как «номера сайта».
const CALLTRACKING_SCRIPT_URL = process.env.NEXT_PUBLIC_CALLTRACKING_SCRIPT_URL || "";

function getScriptSrc() {
  if (!CALLTRACKING_SCRIPT_URL) return "";
  const separator = CALLTRACKING_SCRIPT_URL.includes("?") ? "&" : "?";
  const nc = Math.floor(Date.now() / 300000);
  return `${CALLTRACKING_SCRIPT_URL}${separator}nc=${nc}`;
}

// src зависит от Date.now(), поэтому на сервере и при гидратации отдаём пустую
// строку (snapshot сервера), а клиентское значение React подставляет сам после
// гидратации — без useEffect + setState (правило react-hooks/set-state-in-effect).
const subscribe = () => () => {};
const getServerSnapshot = () => "";

export default function CalltrackingScript() {
  const scriptSrc = useSyncExternalStore(subscribe, getScriptSrc, getServerSnapshot);

  if (!scriptSrc) return null;

  return <Script id="calltracking-script" src={scriptSrc} strategy="afterInteractive" />;
}
