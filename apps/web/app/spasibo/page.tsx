import type { Metadata } from "next";
import ThankYou from "@/components/ThankYou";

// Страница «Спасибо» (ТЗ п.10): сюда попадает пользователь после отправки
// ЛЮБОЙ формы на сайте. На визит этой страницы настраивается оптимизация
// рекламных кампаний (цель «ThankYou» в Яндекс Метрике).
export const metadata: Metadata = {
  title: "Спасибо за заявку",
  description: "Заявка принята — менеджер свяжется с вами в течение 7 минут.",
  robots: {
    index: false,
    follow: false,
  },
};

export default function ThankYouPage() {
  return <ThankYou />;
}
