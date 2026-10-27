# Бесплатное тестирование мобильного приложения на своих телефонах

Как запустить приложение «Точка Чистоты» (`apps/mobile`, Expo) на **физическом iPhone и
Android-телефоне** без платных аккаунтов разработчика (Apple Developer Program за $99/год не
нужен). Актуально на сентябрь 2026.

---

## 0. Коротко

```bash
# 1. Backend, доступный с телефона (любой из вариантов):
make up                     # Docker: web + api + postgres + redis, порт 8000 открыт наружу
make api-dev-lan            # или без Docker: uvicorn на 0.0.0.0:8000 (нужен активный venv)

# 2. Metro для Expo Go (IP компьютера подставится в адрес API сам):
npm run mobile:go           # телефон и компьютер в одной Wi-Fi-сети
npm run mobile:tunnel       # телефон в другой сети / гостевой Wi-Fi

# 3. На телефоне: установить Expo Go (SDK 54) и отсканировать QR-код из терминала.
```

| Платформа | Бесплатный способ | Что нужно | Ограничения |
|---|---|---|---|
| iOS | **Expo Go из App Store** (SDK 54) — сканировать QR камерой | только телефон и Wi-Fi | нативные модули вне Expo Go недоступны (сейчас все используемые — доступны) |
| iOS | **Xcode + Personal Team** (`npm run mobile:ios:device`) | Mac с Xcode 26, iPhone по USB, бесплатный Apple ID | сертификат живёт 7 дней, до 3 приложений, до 10 устройств; переустановка — одной командой |
| Android | **Expo Go** (Google Play или APK для SDK 54) — сканировать QR из Expo Go | телефон и Wi-Fi | как у iOS |
| Android | **APK через EAS Build** (`npm run mobile:apk`) — установка по ссылке/QR без USB | бесплатный аккаунт Expo | очередь и квота сборок бесплатного тарифа; APK ходит в боевой API (см. §5) |
| Android | Отладочная сборка по USB (`npm run android`) | Android Studio (SDK + JDK 17), USB-отладка | на этом Mac Android SDK не установлен — см. §3.3 |

Почему так: Expo Go в App Store и Google Play сейчас поддерживает **только SDK 54**
(для более новых SDK на iOS Expo предлагает `eas go` через TestFlight — это платный
Apple Developer Program). Поэтому приложение обновлено с SDK 51 до **SDK 54**
(React Native 0.81, React 19.1, Expo Router 6): SDK 51 не открывался в текущем Expo Go и
не собирался Xcode 26. Все используемые модули (`expo-router`, `expo-secure-store`,
`expo-linking`, `expo-constants`) входят в Expo Go.

---

## 1. Подготовка компьютера (один раз)

```bash
# Node 22+ и npm (см. корневой package.json)
cd apps/mobile && npm install         # lockfile уже под SDK 54
npx expo-doctor                       # должно быть 18/18 checks passed
cp .env.example .env                  # адрес API для симуляторов; для телефонов подставляется сам
```

Backend должен слушать **все интерфейсы**, а не `localhost` — иначе телефон до него не
достучится:

- Docker (`make up`): порт `8000` уже опубликован наружу (`0.0.0.0:8000`).
- Без Docker: `make api-dev-lan` (это `uvicorn --host 0.0.0.0 --port 8000`).
- Проверка с компьютера: `curl http://$(ipconfig getifaddr en0):8000/api/v1/health`
  (Linux: `hostname -I`). Должен вернуться `{"status":"ok",...}`.
- macOS при первом запуске спросит «Разрешить входящие подключения?» для `node`/`python` —
  разрешите (иначе телефон не увидит ни Metro, ни API).

Telegram/SMS/S3 в локальном backend работают в mock-режиме: код OTP приходит в ответе
`debug_code`, приложение подставляет его само.

---

## 2. Как это работает (сеть)

`npm run go` запускает `apps/mobile/scripts/dev.mjs`:

1. определяет IP компьютера в локальной сети (Wi-Fi `en0`, можно переопределить `HOST_IP=…`);
2. выставляет `EXPO_PUBLIC_API_URL=http://<IP>:8000/api/v1` (переменная из `.env` не мешает —
   приоритет у окружения) и проверяет `GET /health`;
3. запускает `expo start --go --lan` (или `--tunnel`) и печатает QR-код.

Варианты адреса API:

| Ситуация | Команда |
|---|---|
| Телефон и компьютер в одной Wi-Fi-сети (дом/офис) | `npm run go` |
| Телефон в другой сети, но API нужен локальный | `npm run go:api-tunnel` — поднимает публичный HTTPS-туннель до `localhost:8000` (`cloudflared` без аккаунта: `brew install cloudflared`; или `ngrok` — бесплатный аккаунт + `ngrok config add-authtoken …`) |
| Тестировать против боевого API | `node scripts/dev.mjs --api https://api.cleanliness.pro/api/v1` (заявки попадут в реальную CRM) |
| Другой порт API | `API_PORT=8001 npm run go` |

Metro и API — разные соединения: `--tunnel` делает доступным только Metro (JS-бандл),
для API нужен либо общий Wi-Fi, либо `--api-tunnel`, либо боевой адрес.

Незашифрованный HTTP к IP в локальной сети разрешён: в Expo Go — всегда; в собственных
сборках — через `NSAllowsLocalNetworking` (iOS, `app.json`) и стандартный debug-манифест
Android (`usesCleartextTraffic`). Release-сборки (APK из EAS) ходят только по HTTPS —
поэтому профили в `eas.json` собираются с боевым адресом API.

---

## 3. Android

### 3.1 Expo Go (без USB, без аккаунтов)

1. Установите Expo Go: Google Play — «Expo Go» (сейчас это версия для SDK 54). Если магазин
   уже выдаёт более новый SDK и приложение не открывается («Project is incompatible with this
   version of Expo Go»), поставьте APK для SDK 54 напрямую:
   <https://expo.dev/go?sdkVersion=54&platform=android&device=true>
   (загрузка с GitHub-релизов Expo; разрешите установку из неизвестных источников).
2. Подключите телефон к той же Wi-Fi-сети, что и компьютер.
3. На компьютере: `npm run mobile:go`.
4. В Expo Go: «Scan QR code» → наведите на QR из терминала. Приложение загрузится и
   обновляется при каждом сохранении файла (Fast Refresh).
5. Телефон в другой сети: `npm run mobile:tunnel` (Metro через туннель Expo, аккаунт не нужен)
   и при необходимости `npm --prefix apps/mobile run go:api-tunnel` для API.

### 3.2 APK для установки без Metro (EAS Build, облако, бесплатный тариф)

Подходит, чтобы отдать сборку тестерам или проверить приложение «как из магазина».

```bash
npx eas login                         # бесплатный аккаунт expo.dev (проект уже привязан: projectId в app.json)
npm run mobile:apk                    # = eas build --platform android --profile preview
```

По завершении EAS покажет ссылку и QR на `.apk`: откройте на телефоне, разрешите установку из
этого источника, установите. `preview`-профиль собирает release-APK с боевым API
(`EXPO_PUBLIC_API_URL=https://api.cleanliness.pro/api/v1` в `eas.json`) — заявки уходят в
реальную CRM. Бесплатный тариф EAS ограничивает число сборок в месяц и ставит их в общую очередь
(см. expo.dev/pricing); для частых итераций используйте Expo Go.

Локальная сборка без облака (`npm --prefix apps/mobile run android:apk:local`) требует
установленного Android SDK и JDK 17 — см. §3.3.

### 3.3 USB-отладка и локальные сборки (опционально)

Нужно только для `npm run android` (debug-сборка на телефон по USB) и локальных EAS-сборок.
На этом Mac Android SDK и JDK 17 сейчас **не установлены** (`java` = 1.8), поэтому:

1. Установите Android Studio (<https://developer.android.com/studio>) → SDK Manager:
   Android SDK Platform 35+, Build-Tools, Platform-Tools; JDK 17 ставится вместе со студией.
2. В `~/.zshrc`:
   ```bash
   export ANDROID_HOME=$HOME/Library/Android/sdk
   export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator
   export JAVA_HOME=/Applications/Android\ Studio.app/Contents/jbr/Contents/Home
   ```
3. На телефоне: Настройки → О телефоне → 7 раз нажать «Номер сборки» → появится раздел
   «Для разработчиков» → включите «Отладка по USB». Подключите кабель, подтвердите отпечаток
   компьютера; `adb devices` должен показать устройство.
4. `cd apps/mobile && npm run android` — соберёт debug-APK, установит и запустит с Metro.
   Отладочная сборка разрешает HTTP к локальному API; адрес подставьте через `.env` или
   `EXPO_PUBLIC_API_URL=http://<IP>:8000/api/v1 npm run android`.

---

## 4. iOS

### 4.1 Expo Go (без USB, без аккаунта разработчика) — основной способ

1. App Store → «Expo Go» (версия для SDK 54).
2. iPhone и Mac — в одной Wi-Fi-сети.
3. `npm run mobile:go` → наведите **штатную камеру** iPhone на QR-код → «Открыть в Expo Go».
   Можно и вручную: Expo Go → «Enter URL manually» → `exp://<IP>:8081`.
4. Другая сеть — `npm run mobile:tunnel` (+ `go:api-tunnel` для API).

Ограничения Expo Go: нельзя добавить нативные модули, которых нет в Expo Go (карты Яндекс/2ГИС,
платёжные SDK и т.п. — они появятся в Phase 4 плана и потребуют dev-сборку). Для текущего
приложения ограничений нет.

### 4.2 Xcode Free Personal Team — сборка на iPhone по USB (7-дневная подпись)

Бесплатный Apple ID даёт «Personal Team»: Xcode подписывает приложение сертификатом, который
действует 7 дней (потом просто пересобрать), не более 3 приложений на устройстве и 10 устройств
в неделю. Подходит для проверки собственной сборки (dev client, будущие нативные модули).

Один раз:

1. Xcode 26 установлен (`xcode-select -p` → `/Applications/Xcode.app/…`), CocoaPods есть
   (`pod --version`). SDK 54 совместим с Xcode 26.6 (`npx expo-doctor` проходит).
2. Xcode → Settings → Accounts → «+» → войдите своим Apple ID (бесплатный). В списке команд
   появится «Ваше Имя (Personal Team)»; запомните Team ID (10 символов).
3. На iPhone (iOS 16+): Настройки → Конфиденциальность и безопасность → **Режим разработчика** →
   включить, перезагрузить, подтвердить.
4. Подключите iPhone кабелем, нажмите «Доверять этому компьютеру».

Сборка и запуск:

```bash
cd apps/mobile
APPLE_TEAM_ID=XXXXXXXXXX npm run ios:device      # = APP_VARIANT=dev expo run:ios --device
```

- `APP_VARIANT=dev` (уже в скрипте) даёт bundle id `com.belofflab.tochka.dev` и имя
  «Точка Чистоты (dev)» — личная сборка не конфликтует с релизным id, зарегистрированным в
  команде компании.
- Первый запуск генерирует `ios/` (`expo prebuild`), ставит CocoaPods и предлагает выбрать
  устройство; `APPLE_TEAM_ID` подставляется в проект (`ios.appleTeamId`). Если Xcode
  ругается на подпись — откройте `ios/*.xcworkspace`, target → Signing & Capabilities →
  «Automatically manage signing» → Team: Personal Team, и повторите команду.
- На iPhone после первой установки: Настройки → Основные → VPN и управление устройством →
  ваш Apple ID → «Доверять».
- Metro запускается автоматически; адрес API задайте заранее:
  `EXPO_PUBLIC_API_URL=http://<IP-Mac>:8000/api/v1 APPLE_TEAM_ID=… npm run ios:device`
  (HTTP к локальной сети разрешён через `NSAllowsLocalNetworking` в `app.json`).
- Через 7 дней приложение перестанет запускаться — повторите команду (устройство уже
  доверенное, занимает минуту).

### 4.3 AltStore / SideStore (альтернатива, без Mac под рукой)

Тот же 7-дневный сертификат бесплатного Apple ID, но подписывает и обновляет приложение
AltStore на телефоне. Нужен `.ipa`: соберите приложение для устройства в Xcode
(Product → Build, Personal Team), возьмите `Точка Чистоты (dev).app` из
`~/Library/Developer/Xcode/DerivedData/…/Build/Products/Debug-iphoneos/`, положите в папку
`Payload/` и заархивируйте в `.ipa` (`zip -r app.ipa Payload`). Далее — по инструкции
AltStore (<https://altstore.io>) или SideStore (<https://sidestore.io>). Для регулярного
тестирования проще §4.1 или §4.2.

---

## 5. Адрес API и данные

- Локальный API (`make up`) с сидами: `make seed` — города Уфа/Тюмень, услуги, слоты мастеров,
  промокод `CLEAN10`. OTP приходит в `debug_code` (SMS выключен). Заявки остаются в вашей
  локальной БД — безопасно для экспериментов.
- Боевой API (`--api https://api.cleanliness.pro/api/v1`, а также все APK/AAB из EAS): реальные
  лиды в CRM и Telegram-пинги операторам, реальные SMS при включённом `SMS_ENABLED`. Используйте
  только для приёмочных проверок.
- Город по умолчанию — `EXPO_PUBLIC_DEFAULT_CITY` (`ufa`), совпадает с `DEFAULT_CITY_SLUG` бэкенда.

---

## 6. Если что-то не работает

| Симптом | Причина / решение |
|---|---|
| QR не открывается, «Something went wrong» / «Could not connect to the server» | Телефон и компьютер в разных сетях или Wi-Fi изолирует клиентов (гостевые сети, офисные VLAN). Используйте `npm run mobile:tunnel`. |
| Приложение открылось, но «Не удалось отправить код» / расчёт не считается | Телефон не видит API. Проверьте баннер `API: … ✗ недоступен` при старте, что backend слушает `0.0.0.0` (`make up` / `make api-dev-lan`), файрвол macOS разрешил входящие для `python`/`node`, IP определён верно (`HOST_IP=…`). Для другой сети — `go:api-tunnel`. |
| «Project is incompatible with this version of Expo Go» | Версия Expo Go не под SDK 54: Android — APK по ссылке из §3.1; iOS — обновите/переустановите Expo Go из App Store. Если магазин перешёл на более новый SDK, обновите проект (`npm install expo@<версия> && npx expo install --fix`) — только когда обе платформы Expo Go поддерживают новый SDK. |
| Metro пишет «port 8081 already in use» | `node scripts/dev.mjs -- --port 8082` (в Expo Go введите новый URL) или закройте старый процесс. |
| Странные ошибки после обновления зависимостей | `npx expo start --clear` (сброс кеша Metro), `npx expo-doctor`, `rm -rf node_modules && npm install`. |
| Metro: `Cannot find module 'babel-preset-expo'` | В SDK 54 пресет должен быть явной зависимостью проекта (уже в `devDependencies`); если пропал после ручных правок — `npx expo install babel-preset-expo`. Быстрая проверка бандлов: `npm run export:check`. |
| iOS: «Untrusted Developer» / приложение не запускается | Настройки → Основные → VPN и управление устройством → доверять; включён ли Режим разработчика; не истекли ли 7 дней (пересоберите). |
| Симулятор iOS: предупреждение «SecureStore недоступен» | Keychain не работает в неподписанной сборке (`xcodebuild … CODE_SIGNING_ALLOWED=NO`). `npm run ios` подписывает симуляторную сборку автоматически; на телефонах и в Expo Go хранилище работает. Приложение в этом случае держит токены в памяти до перезапуска. |
| iOS: Xcode «No profiles for 'com.belofflab.tochka.dev'» / «bundle identifier is not available» | В Signing выберите Personal Team и «Automatically manage signing»; при конфликте id измените суффикс в `app.config.js` (например `.dev2`). |
| Android: «Заблокировано Play Protect» при установке APK | «Подробнее» → «Всё равно установить» (сборка не из магазина). |
| Android: APK ставится, но API «недоступен» | Release-APK ходит только по HTTPS — это боевой API из `eas.json`; для локального API используйте Expo Go или debug-сборку по USB. |
| `--tunnel` не стартует | Нужен доступ в интернет; `@expo/ngrok` уже в devDependencies; при корпоративном прокси — LAN-режим. |

---

## 7. Справочник команд

| Команда (из корня) | Что делает |
|---|---|
| `npm run mobile:go` | Metro для Expo Go в локальной сети, API = IP компьютера |
| `npm run mobile:tunnel` | Metro через туннель Expo |
| `npm --prefix apps/mobile run go:api-tunnel` | + HTTPS-туннель до локального API (cloudflared/ngrok) |
| `npm run mobile:apk` | APK через EAS Build (бесплатный тариф) |
| `npm run mobile:ios:device` | iPhone по USB, Personal Team (`APPLE_TEAM_ID=…`) |
| `npm run mobile:doctor` | `expo-doctor` — здоровье проекта и совместимость тулчейнов |
| `npm --prefix apps/mobile run typecheck` | `tsc --noEmit` |
| `npm --prefix apps/mobile run export:check` | JS-бандлы iOS/Android без нативных тулчейнов (то, что гоняет CI) |
| `make api-dev-lan` | API без Docker на `0.0.0.0:8000` |

Настройки, которые делают это возможным: `apps/mobile/scripts/dev.mjs` (IP/туннели),
`app.json` (`NSAllowsLocalNetworking`, New Architecture), `app.config.js` (`APP_VARIANT=dev`,
`APPLE_TEAM_ID`), `eas.json` (`preview` = APK), `@expo/ngrok` в devDependencies (туннель без
интерактивной установки).
