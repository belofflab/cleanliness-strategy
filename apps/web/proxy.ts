import { NextRequest, NextResponse } from "next/server";
import {
  DEFAULT_CITY_SLUG,
  getCitySlugFromHost,
  getCitySlugFromPathname,
  isCitySlug,
  isKnownCitySlug,
  normalizeCitySlug,
} from "@/lib/city";

const EXCLUDED_PATH_PREFIXES = [
  "/api",
  "/_next",
  "/favicon.ico",
  "/robots.txt",
  "/sitemap.xml",
  "/manifest.json",
  "/icons",
  "/images",
  "/logos",
  "/apple-touch-icon.png",
];

function isPublicFile(pathname: string) {
  return /\.[^/]+$/.test(pathname);
}

function shouldBypass(pathname: string) {
  return EXCLUDED_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix)) || isPublicFile(pathname);
}

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  if (shouldBypass(pathname)) {
    return NextResponse.next();
  }

  // Общие страницы без региональной подмены пути. «/spasibo» — единый URL
  // после отправки любой формы: на него настраивается оптимизация РК (ТЗ п.10).
  if (
    pathname.startsWith("/oferta") ||
    pathname.startsWith("/privacy") ||
    pathname.startsWith("/spasibo")
  ) {
    return NextResponse.next();
  }

  // Админ-CRM — отдельная зона, без региональной подмены пути.
  if (pathname.startsWith("/admin")) {
    return NextResponse.next();
  }

  // Известный, но временно отключённый город (например /tyumen) —
  // мягкий временный редирект на главную (город по умолчанию).
  const firstSegment = pathname.split("/").filter(Boolean)[0];
  if (firstSegment && isKnownCitySlug(firstSegment) && !isCitySlug(firstSegment)) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/";
    return NextResponse.redirect(redirectUrl, 302);
  }

  const cityFromPath = getCitySlugFromPathname(pathname);
  if (cityFromPath) {
    const response = NextResponse.next();
    response.cookies.set("city_slug", cityFromPath, {
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
      sameSite: "lax",
    });
    return response;
  }

  const cityFromHost = getCitySlugFromHost(request.headers.get("host"));
  const cityFromHeader = request.headers.get("x-city-slug");
  const cityFromCookie = request.cookies.get("city_slug")?.value;
  const citySlug = normalizeCitySlug(cityFromHost ?? cityFromHeader ?? cityFromCookie ?? DEFAULT_CITY_SLUG);

  const rewriteUrl = request.nextUrl.clone();
  rewriteUrl.pathname = `/${citySlug}${pathname === "/" ? "" : pathname}`;

  const response = NextResponse.rewrite(rewriteUrl);
  response.cookies.set("city_slug", citySlug, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|xml|txt)$).*)"],
};
