# Точка Чистоты — Mobile (Expo / React Native)

Клиентское мобильное приложение: OTP-вход, оформление заявки на уборку
(динамический расчёт + выбор слота), профиль. Работает с тем же backend, что и web
(`/api/v1`). Целевая архитектура (потоки Клиент/Клинер) — `docs/SYSTEM_AUDIT.md`.

**Тестирование на своих телефонах без платных аккаунтов разработчика —
[`docs/FREE_TESTING_GUIDE.md`](../../docs/FREE_TESTING_GUIDE.md).**

## Стек
- Expo SDK 54 (React Native 0.81, React 19.1, New Architecture), Expo Router 6 (file-based)
- TypeScript (strict)
- expo-secure-store — токены в Keychain/Keystore
- Прозрачная ротация access-токена через `/auth/refresh`

> SDK 54 — единственная версия, для которой Expo Go доступен бесплатно и в App Store,
> и в Google Play (более новые SDK на iOS требуют `eas go` и платный Apple Developer Program).
> Не обновляйте SDK без проверки этого условия.

## Структура
```
apps/mobile/
├─ app/                      # экраны (Expo Router)
│  ├─ _layout.tsx            # AuthProvider + корневой стек
│  ├─ index.tsx             # сплэш-редирект по статусу авторизации
│  ├─ (auth)/login.tsx      # OTP-вход (телефон → код)
│  └─ (tabs)/
│     ├─ _layout.tsx        # таб-навигация + auth-guard
│     ├─ index.tsx          # заявка: расчёт + слоты + бронирование
│     └─ profile.tsx        # профиль + выход
├─ src/
│  ├─ api/client.ts         # HTTP-клиент + refresh
│  ├─ api/types.ts          # DTO (зеркало FastAPI-схем)
│  ├─ api/storage.ts        # SecureStore-хранилище токенов
│  ├─ auth/AuthContext.tsx  # глобальный auth-стейт
│  └─ theme.ts
├─ scripts/dev.mjs          # запуск Metro для телефонов: IP машины → EXPO_PUBLIC_API_URL
├─ app.json                 # конфиг приложения (bundleId/package, ATS, New Architecture)
├─ app.config.js            # варианты: APP_VARIANT=dev (…​.dev), APPLE_TEAM_ID
├─ eas.json                 # профили сборки EAS (preview = APK для тестеров)
└─ .env.example
```

## Эндпоинты, которые использует приложение
| Действие            | Метод | Путь                       |
|---------------------|-------|----------------------------|
| Запрос OTP          | POST  | `/auth/otp/request`        |
| Подтверждение OTP   | POST  | `/auth/otp/verify`         |
| Обновление токена   | POST  | `/auth/refresh`            |
| Профиль             | GET   | `/auth/me`                 |
| Выход               | POST  | `/auth/logout`             |
| Расчёт стоимости    | POST  | `/pricing/quote`           |
| Свободные слоты     | GET   | `/booking/availability`    |
| Оформление заявки   | POST  | `/booking/bookings`        |

## Команды
```bash
cd apps/mobile
npm install                 # зависимости (lockfile синхронен с SDK 54)
cp .env.example .env        # адрес API для симуляторов; для телефонов подставляется сам

npm run go                  # Metro для Expo Go, телефон в той же Wi-Fi-сети
npm run go:tunnel           # Metro через туннель Expo (телефон в другой сети)
npm run go:api-tunnel       # + публичный HTTPS-туннель до локального API (cloudflared/ngrok)
npm run ios                 # симулятор iOS (Xcode)
npm run ios:device          # iPhone по USB, бесплатная подпись Personal Team (см. гайд)
npm run android:apk         # APK через EAS Build (облако, бесплатный тариф)
npm run typecheck           # tsc --noEmit
npm run doctor              # expo-doctor
npm run export:check        # сборка JS-бандлов iOS/Android (проверка без нативных тулчейнов)
```
Из корня монорепо: `npm run mobile:go`, `npm run mobile:tunnel`, `npm run mobile:apk`,
`make mobile-go`, `make api-dev-lan`.

## Релиз (справочно)
- Android: `eas build --platform android --profile production` (AAB для Google Play).
- iOS: `eas build --platform ios --profile production` — требует Apple Developer Program.
- OTA-обновления после релиза: `eas update --branch production --message "hotfix"`.
- Перед релизом: свои иконки/сплэш (`assets/`), `version`/`buildNumber`/`versionCode`
  (в production-профиле включён `autoIncrement`).
