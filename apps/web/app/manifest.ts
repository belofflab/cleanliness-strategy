import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Точка Чистоты",
    short_name: "Точка Чистоты",
    description: "Премиальный клининг в Уфе: квартиры, дома, офисы.",
    start_url: "/",
    display: "standalone",
    background_color: "#f4f8fb",
    theme_color: "#0ea5e9",
    lang: "ru",
    icons: [
      {
        src: "/favicon.ico",
        sizes: "any",
        type: "image/x-icon",
      },
    ],
  };
}

