import type { MetadataRoute } from "next";
import { ACTIVE_CITY_SLUGS, DEFAULT_CITY_SLUG } from "@/lib/city";
import { getCityCanonicalUrl, getRegionalLandingEntries } from "@/lib/seo";
import { SERVICE_LANDING_SLUGS } from "@/lib/service-landings";

const now = new Date();

export default function sitemap(): MetadataRoute.Sitemap {
  const regionalEntries = getRegionalLandingEntries().map(({ citySlug, url }) => ({
    url,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: citySlug === DEFAULT_CITY_SLUG ? 1 : 0.95,
  }));

  // Посадочные услуг (фаза 2 SEO): по каждой услуге в каждом активном городе.
  const serviceEntries = ACTIVE_CITY_SLUGS.flatMap((citySlug) =>
    SERVICE_LANDING_SLUGS.map((serviceSlug) => ({
      url: getCityCanonicalUrl(citySlug, `/${serviceSlug}`),
      lastModified: now,
      changeFrequency: "weekly" as const,
      priority: citySlug === DEFAULT_CITY_SLUG ? 0.9 : 0.85,
    })),
  );

  return [
    ...regionalEntries,
    ...serviceEntries,
    {
      url: getCityCanonicalUrl(DEFAULT_CITY_SLUG, "/oferta"),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.4,
    },
    {
      url: getCityCanonicalUrl(DEFAULT_CITY_SLUG, "/privacy"),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.4,
    },
  ];
}

