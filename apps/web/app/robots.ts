import type { MetadataRoute } from "next";
import { DEFAULT_CITY_SLUG } from "@/lib/city";
import { getCityCanonicalUrl, getRegionalSitemapUrls } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Служебные разделы не для выдачи: админ-CRM и страница «Спасибо»
      // (она noindex, но disallow экономит краул-бюджет).
      disallow: ["/admin", "/spasibo"],
    },
    sitemap: getRegionalSitemapUrls(),
    host: getCityCanonicalUrl(DEFAULT_CITY_SLUG, "/"),
  };
}

