// Динамическая конфигурация поверх app.json — варианты для бесплатного
// тестирования на своих телефонах (см. docs/FREE_TESTING_GUIDE.md).
//
//   APP_VARIANT=dev  → отдельный bundle id / package (`…​.dev`) и имя «Точка Чистоты (dev)»:
//                      личная (Xcode Personal Team) или отладочная сборка ставится рядом
//                      с релизной и не конфликтует с bundle id, зарегистрированным в другой
//                      команде Apple;
//   APPLE_TEAM_ID    → команда подписи для `expo run:ios --device` (ID Personal Team из
//                      Xcode → Settings → Accounts); без него команду выбирают в Xcode вручную.
//
// Без переменных конфигурация равна app.json (релиз, EAS Build, Expo Go).
module.exports = ({ config }) => {
  const isDev = process.env.APP_VARIANT === "dev";
  const suffix = isDev ? ".dev" : "";
  const appleTeamId = process.env.APPLE_TEAM_ID;

  return {
    ...config,
    name: isDev ? `${config.name} (dev)` : config.name,
    ios: {
      ...config.ios,
      bundleIdentifier: `${config.ios.bundleIdentifier}${suffix}`,
      ...(appleTeamId ? { appleTeamId } : {}),
    },
    android: {
      ...config.android,
      package: `${config.android.package}${suffix}`,
    },
  };
};
