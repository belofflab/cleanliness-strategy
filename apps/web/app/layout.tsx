import type { Metadata, Viewport } from "next";
import { Inter, Manrope } from "next/font/google";
import { getSiteUrl } from "@/lib/site";
import "./globals.css";

import CalltrackingScript from "@/components/CalltrackingScript";
import YandexMetrika from "@/components/YandexMetrika";
import {Suspense} from "react";
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const siteUrl = getSiteUrl();

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Точка Чистоты — Премиальный клининг в Уфе",
    template: "%s | Точка Чистоты",
  },
  description:
    "Премиальный клининг квартир, домов и офисов в Уфе. Быстрый расчёт стоимости, быстрый выезд, гарантия качества и удобная связь в мессенджерах.",
  keywords: [
    "клининг Уфа",
    "уборка квартиры Уфа",
    "клининг Тюмень",
    "уборка квартиры Тюмень",
    "генеральная уборка",
    "уборка после ремонта",
    "Точка Чистоты",
  ],
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Точка Чистоты — Премиальный клининг в Уфе",
    description:
      "Современный клининговый сервис в Уфе: прозрачная цена, быстрый выезд и контроль качества на каждом этапе.",
    type: "website",
    locale: "ru_RU",
    url: siteUrl,
    siteName: "Точка Чистоты",
  },
  twitter: {
    card: "summary_large_image",
    title: "Точка Чистоты — Премиальный клининг в Уфе",
    description:
      "Быстрый расчёт стоимости уборки, быстрый выезд и удобная связь через Telegram и Max в Уфе.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  category: "cleaning services",
};

export const viewport: Viewport = {
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${inter.variable} ${manrope.variable} h-full antialiased`}>
      {/* Метрика — строго ВНУТРИ body: <noscript> прямым потомком <html> вызывал
          hydration-ошибку на каждой загрузке (нестабильность из ТЗ п.11). */}
      <body className="min-h-full flex flex-col">
        {children}
        <Suspense fallback={null}>
          <YandexMetrika />
        </Suspense>
        {/* Подмена номеров: грузится только при заданном NEXT_PUBLIC_CALLTRACKING_SCRIPT_URL. */}
        <CalltrackingScript />
      </body>
    </html>
  );
}
