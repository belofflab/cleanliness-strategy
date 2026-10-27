const DEFAULT_SITE_URL = "http://localhost:3000";

function normalizeUrl(value: string) {
  if (!value) return DEFAULT_SITE_URL;
  if (value.startsWith("http://") || value.startsWith("https://")) return value;
  return `https://${value}`;
}

export function getSiteUrl() {
  const envUrl =
    process.env.NEXT_PUBLIC_SITE_URL ||
    process.env.VERCEL_PROJECT_PRODUCTION_URL ||
    process.env.VERCEL_URL ||
    "";

  return normalizeUrl(envUrl);
}

