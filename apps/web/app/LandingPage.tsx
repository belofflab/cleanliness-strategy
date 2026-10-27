import App from "@/app/App";
import { DEFAULT_CITY_SLUG, normalizeCitySlug } from "@/lib/city";

type LandingPageProps = {
  citySlug?: string;
};

// Структурированные данные (LocalBusiness/FAQ) рендерит CityJsonLd на уровне
// страниц — здесь только приложение. Выдуманные aggregateRating из старой
// разметки удалены: рейтинги без подтверждённых отзывов на странице ведут
// к ручным санкциям Google за спам-разметку.
export default function LandingPage({ citySlug = DEFAULT_CITY_SLUG }: LandingPageProps) {
  const resolvedCitySlug = normalizeCitySlug(citySlug);

  return <App initialCitySlug={resolvedCitySlug} />;
}
