"use client";

import { useEffect } from "react";
import { logError } from "@/lib/logger";

// Глобальная граница ошибок App Router. Логирует ошибку структурно
// (одной JSON-строкой) — на сервере это уходит в stdout контейнера → Promtail.
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    logError(error, { scope: "global-error", digest: error.digest });
  }, [error]);

  return (
    <html lang="ru">
      <body
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, sans-serif",
          background: "#f4f8fb",
          color: "#0f172a",
        }}
      >
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 600 }}>Что-то пошло не так</h1>
          <p style={{ marginTop: "0.5rem", color: "#5f6b7a" }}>
            Мы уже знаем о проблеме. Попробуйте обновить страницу.
          </p>
          <button
            type="button"
            onClick={reset}
            style={{
              marginTop: "1.5rem",
              borderRadius: "0.75rem",
              background: "#0f172a",
              color: "#fff",
              padding: "0.625rem 1.25rem",
              fontWeight: 600,
            }}
          >
            Обновить
          </button>
        </div>
      </body>
    </html>
  );
}
