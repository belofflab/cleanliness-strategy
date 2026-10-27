import { notFound } from "next/navigation";
import LandingPage from "@/app/LandingPage";
import CityJsonLd from "@/components/CityJsonLd";
import { ACTIVE_CITY_SLUGS, isCitySlug } from "@/lib/city";

type CityPageProps = {
  params: Promise<{ city: string }>;
};

export default async function CityPage({ params }: CityPageProps) {
  const { city } = await params;

  if (!isCitySlug(city)) {
    notFound();
  }

  return (
    <>
      <CityJsonLd citySlug={city} />
      <LandingPage citySlug={city} />
    </>
  );
}

export async function generateStaticParams() {
  return ACTIVE_CITY_SLUGS.map((city) => ({ city }));
}
