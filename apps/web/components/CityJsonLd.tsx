// Структурированные данные (JSON-LD) городской страницы — локальное SEO:
// LocalBusiness-карточка компании (адрес, телефон, график, районы, профили
// на площадках) + каталог услуг с ценами «от» + FAQPage для расширенных
// сниппетов. Рендерится на сервере — поисковики видят разметку без JS.

import { getCityProfile, type CitySlug } from "@/lib/city";
import { getCityCanonicalUrl } from "@/lib/seo";
import { FAQ_ITEMS } from "@/lib/faq";

// Стартовые цены услуг «от» — синхронизированы с сидами каталога (Уфа).
const SERVICE_OFFERS = [
  { name: "Поддерживающая уборка", price: 1650 },
  { name: "Генеральная уборка", price: 3750 },
  { name: "Уборка после ремонта", price: 5350 },
  { name: "Офисная уборка", price: 2650 },
];

export default function CityJsonLd({ citySlug }: { citySlug: CitySlug }) {
  const city = getCityProfile(citySlug);
  const canonical = getCityCanonicalUrl(citySlug, "/");

  const business = {
    "@context": "https://schema.org",
    "@type": "HomeAndConstructionBusiness",
    "@id": `${canonical}#business`,
    name: `Точка Чистоты — клининг ${city.namePrepositional}`,
    description: `Профессиональная уборка квартир, домов и офисов ${city.namePrepositional}: поддерживающая, генеральная, после ремонта. Свои средства и инвентарь, оплата после приёмки.`,
    url: canonical,
    telephone: city.phone,
    email: city.email,
    image: `${canonical.replace(/\/$/, "")}/icon.svg`,
    priceRange: "₽₽",
    address: {
      "@type": "PostalAddress",
      addressLocality: city.locality,
      streetAddress: city.primaryBranchAddress,
      addressCountry: "RU",
    },
    areaServed: city.districts.map((district) => ({
      "@type": "AdministrativeArea",
      name: `${city.locality}, ${district}`,
    })),
    openingHoursSpecification: {
      "@type": "OpeningHoursSpecification",
      dayOfWeek: [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
      ],
      opens: "08:00",
      closes: "22:00",
    },
    sameAs: [city.yandexBusinessUrl, city.twoGisUrl, "https://t.me/pointclean"],
    makesOffer: SERVICE_OFFERS.map((offer) => ({
      "@type": "Offer",
      itemOffered: { "@type": "Service", name: offer.name },
      priceSpecification: {
        "@type": "PriceSpecification",
        price: offer.price,
        priceCurrency: "RUB",
        description: "Стартовая цена; точную стоимость согласуем до начала работ",
      },
    })),
  };

  const faq = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ_ITEMS.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(business) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faq) }}
      />
    </>
  );
}
