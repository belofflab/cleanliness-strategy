// Лёгкий структурный логгер фронтенда.
// Пишет ОДНУ JSON-строку в console.* — серверный вывод Next.js (Node) попадает
// в stdout/stderr контейнера, откуда его читает Promtail (тот же формат, что и
// у бэкенда: timestamp/level/message + контекст).

type Level = "error" | "warn" | "info";

type LogContext = Record<string, unknown>;

function emit(level: Level, message: string, context?: LogContext) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    service: "web",
    message,
    ...context,
  };
  const line = JSON.stringify(entry);
  // Уровни осознанно маппятся на разные потоки (stdout/stderr).
  if (level === "error") console.error(line);
  else if (level === "warn") console.warn(line);
  else console.log(line);
}

export const logger = {
  error: (message: string, context?: LogContext) => emit("error", message, context),
  warn: (message: string, context?: LogContext) => emit("warn", message, context),
  info: (message: string, context?: LogContext) => emit("info", message, context),
};

/** Структурно логирует пойманную ошибку (с message/stack/name). */
export function logError(error: unknown, context?: LogContext) {
  const normalized =
    error instanceof Error
      ? { name: error.name, message: error.message, stack: error.stack }
      : { message: String(error) };
  emit("error", normalized.message, { ...context, error: normalized });
}
