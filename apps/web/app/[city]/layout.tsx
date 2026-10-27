import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ACTIVE_CITY_SLUGS, isCitySlug } from "@/lib/city";
import { buildCityMetadata } from "@/lib/seo";

type CityLayoutProps = {
  children: React.ReactNode;
  params: Promise<{ city: string }>;
};

export async function generateMetadata({ params }: CityLayoutProps): Promise<Metadata> {
  const { city } = await params;

  if (!isCitySlug(city)) {
    return {};
  }

  return buildCityMetadata(city);
}

export async function generateStaticParams() {
  return ACTIVE_CITY_SLUGS.map((city) => ({ city }));
}

export default async function CityLayout({ children, params }: CityLayoutProps) {
  const { city } = await params;

  if (!isCitySlug(city)) {
    notFound();
  }

  return children;
}
