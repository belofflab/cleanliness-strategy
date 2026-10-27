import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ServiceLandingView from "@/components/ServiceLandingView";
import { ACTIVE_CITY_SLUGS, getCityProfile, isCitySlug } from "@/lib/city";
import { getCityCanonicalUrl, getCityHreflangMap } from "@/lib/seo";
import {
  getServiceLanding,
  SERVICE_LANDING_SLUGS,
} from "@/lib/service-landings";

// SEO-посадочные услуг: /{city}/{service}. Корневые пути (/uborka-kvartir)
// прокси переписывает на город из поддомена/cookie — как и главную.

type ServicePageProps = {
  params: Promise<{ city: string; service: string }>;
};

export async function generateStaticParams() {
  return ACTIVE_CITY_SLUGS.flatMap((city) =>
    SERVICE_LANDING_SLUGS.map((service) => ({ city, service })),
  );
}

export async function generateMetadata({ params }: ServicePageProps): Promise<Metadata> {
  const { city, service: serviceSlug } = await params;
  const service = getServiceLanding(serviceSlug);

  if (!isCitySlug(city) || !service) return {};

  const cityProfile = getCityProfile(city);
  const path = `/${service.slug}`;
  const priceFrom = service.priceFrom[city];

  return {
    // Бренд добавляем явно: root-template не наследуется через city-layout
    // с собственным строковым title.
    title: `${service.name} ${cityProfile.namePrepositional} — цена от ${priceFrom.toLocaleString("ru-RU")} ₽ | Точка Чистоты`,
    description: `${service.name} ${cityProfile.namePrepositional} от «Точки Чистоты»: свои средства, фиксированная цена до начала работ, оплата после приёмки. Онлайн-расчёт за минуту, выезд в день заявки.`,
    alternates: {
      canonical: getCityCanonicalUrl(city, path),
      languages: getCityHreflangMap(path),
    },
  };
}

export default async function ServiceLandingPage({ params }: ServicePageProps) {
  const { city, service: serviceSlug } = await params;
  const service = getServiceLanding(serviceSlug);

  if (!isCitySlug(city) || !service) {
    notFound();
  }

  const cityProfile = getCityProfile(city);
  const canonical = getCityCanonicalUrl(city, `/${service.slug}`);

  const serviceSchema = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: `${service.name} ${cityProfile.namePrepositional}`,
    serviceType: service.name,
    url: canonical,
    areaServed: { "@type": "City", name: cityProfile.locality },
    provider: {
      "@type": "HomeAndConstructionBusiness",
      name: `Точка Чистоты — клининг ${cityProfile.namePrepositional}`,
      telephone: cityProfile.phone,
      url: getCityCanonicalUrl(city, "/"),
    },
    offers: {
      "@type": "Offer",
      price: service.priceFrom[city],
      priceCurrency: "RUB",
      description: service.priceNote,
    },
  };

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: service.faq.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(serviceSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <ServiceLandingView citySlug={city} service={service} />
    </>
  );
}
