import LandingPage from "@/app/LandingPage";
import CityJsonLd from "@/components/CityJsonLd";
import { DEFAULT_CITY_SLUG } from "@/lib/city";

export default function Home() {
  // Корневая страница = город по умолчанию (сейчас Уфа); фактический город
  // подставляет proxy.ts по субдомену/cookie ещё до рендера.
  return (
    <>
      <CityJsonLd citySlug={DEFAULT_CITY_SLUG} />
      <LandingPage citySlug={DEFAULT_CITY_SLUG} />
    </>
  );
}
