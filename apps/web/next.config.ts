import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // Лёгкий production-образ для Docker: Next копирует только нужные файлы
  // в .next/standalone и генерирует минимальный server.js (см. docs/output.md).
  output: "standalone",
  // Монорепо: трассировка файлов от корня репозитория (docs/output.md → Caveats),
  // иначе standalone не подхватит зависимости из корневого node_modules.
  outputFileTracingRoot: path.join(__dirname, "../../"),
  images: {
    formats: ["image/avif", "image/webp"],
    // Реальные фото «До/После» и аватары мастеров грузятся из Yandex Object Storage.
    remotePatterns: [
      { protocol: "https", hostname: "**.storage.yandexcloud.net" },
      { protocol: "https", hostname: "storage.yandexcloud.net" },
    ],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
