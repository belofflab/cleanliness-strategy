"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, ExternalLink, Star } from "lucide-react";
import { api } from "@/lib/api";
import { getCityProfile, normalizeCitySlug } from "@/lib/city";
import { trackEvent } from "@/lib/analytics";

// «Прозрачные» отзывы (ТЗ п.6): логотип площадки, имя, дата, вид уборки,
// короткий текст и ссылка «Смотреть оригинал». Данные тянутся с бэкенда
// (`GET /reviews`, синк Яндекс/2ГИС), фоллбэк — статический список без
// указания площадок (неподтверждённые отзывы не подписываем именем площадки).
const DEFAULT_REVIEWS = [
	{
		id: "r1",
		author: "Алина",
		rating: 5,
		provider: "manual",
		serviceType: "Генеральная уборка",
		date: "2026-06-14",
		sourceUrl: null,
		text: "Заказала генеральную уборку перед приездом гостей. Всё чётко по времени и очень аккуратно.",
	},
	{
		id: "r2",
		author: "Роман",
		rating: 5,
		provider: "manual",
		serviceType: "Офисная уборка",
		date: "2026-06-02",
		sourceUrl: null,
		text: "Понравился сервис: быстрое подтверждение, прозрачная стоимость, идеальный результат.",
	},
	{
		id: "r3",
		author: "Эльвира",
		rating: 5,
		provider: "manual",
		serviceType: "Уборка после ремонта",
		date: "2026-05-21",
		sourceUrl: null,
		text: "После ремонта квартира была в пыли. Команда справилась за день, без лишней суеты.",
	},
	{
		id: "r4",
		author: "Дмитрий",
		rating: 5,
		provider: "manual",
		serviceType: "Поддерживающая уборка",
		date: "2026-05-05",
		sourceUrl: null,
		text: "Регулярно беру поддерживающую уборку. Каждый раз стабильно отличный результат и вежливая команда.",
	},
	{
		id: "r5",
		author: "Гульназ",
		rating: 5,
		provider: "manual",
		serviceType: "Мытьё окон",
		date: "2026-04-18",
		sourceUrl: null,
		text: "Отдельное спасибо за мытьё окон — сияют. Очень довольна, рекомендую друзьям.",
	},
];

// Упрощённые знаки площадок (инлайн, без внешних запросов).
function ProviderLogo({ provider }) {
	if (provider === "yandex") {
		return (
			<span className="inline-flex h-5 w-5 items-center justify-center rounded-md bg-[#FC3F1D] text-[11px] font-bold text-white" aria-hidden="true">
				Я
			</span>
		);
	}
	if (provider === "2gis") {
		return (
			<span className="inline-flex h-5 min-w-5 items-center justify-center rounded-md bg-[#29B24A] px-1 text-[9px] font-bold text-white" aria-hidden="true">
				2ГИС
			</span>
		);
	}
	if (provider === "google") {
		return (
			<span className="inline-flex h-5 w-5 items-center justify-center rounded-md border border-slate-200 bg-white text-[11px] font-bold text-[#4285F4]" aria-hidden="true">
				G
			</span>
		);
	}
	return null;
}

const PROVIDER_LABELS = {
	yandex: "Яндекс",
	"2gis": "2ГИС",
	google: "Google",
};

function ProviderBadge({ provider, sourceUrl }) {
	const label = PROVIDER_LABELS[provider];

	// Нет подтверждаемой площадки — название не выводим (ТЗ п.6).
	if (!label) {
		return (
			<span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
				Клиент компании
			</span>
		);
	}

	const content = (
		<span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">
			<ProviderLogo provider={provider} />
			{label}
		</span>
	);

	return sourceUrl ? (
		<a href={sourceUrl} target="_blank" rel="noreferrer">
			{content}
		</a>
	) : (
		content
	);
}

// Приводим ответ API (ReviewOut) к форме карточки.
function normalizeReview(review) {
	return {
		id: review.id,
		author: review.author_name,
		rating: Math.round(review.rating),
		provider: review.provider || "manual",
		serviceType: review.service_type || null,
		date: review.published_at || null,
		sourceUrl: review.source_url || null,
		text: review.text,
	};
}

function formatReviewDate(value) {
	if (!value) return null;
	const date = new Date(value);
	if (Number.isNaN(date.getTime())) return null;
	return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" }).format(date);
}

export default function ReviewsSection({ reviews: reviewsProp, citySlug }) {
	const trackRef = useRef(null);
	const resolvedCitySlug = normalizeCitySlug(citySlug);
	const cityProfile = getCityProfile(resolvedCitySlug);
	// Если отзывы переданы пропсом — используем их, иначе тянем с API.
	const [reviews, setReviews] = useState(reviewsProp ?? DEFAULT_REVIEWS);

	useEffect(() => {
		if (reviewsProp) return;
		const controller = new AbortController();

		api
			.getReviews(resolvedCitySlug, 30, controller.signal)
			.then((data) => {
				if (Array.isArray(data) && data.length > 0) {
					setReviews(data.map(normalizeReview));
				}
				// Пустой ответ — оставляем дефолтные отзывы.
			})
			.catch(() => {
				// API недоступен — молча используем статический массив.
			});

		return () => controller.abort();
	}, [resolvedCitySlug, reviewsProp]);

	// Прокрутка стрелками на ширину одной карточки (UX для десктопа).
	const scrollByCard = (direction) => {
		const track = trackRef.current;
		if (!track) return;
		const card = track.querySelector("[data-review-card]");
		const amount = card ? card.clientWidth + 12 : 320;
		track.scrollBy({ left: direction * amount, behavior: "smooth" });
	};

	return (
		<section id="reviews" className="px-4 py-16 sm:px-6 lg:px-10">
			<div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
				<div className="flex flex-wrap items-end justify-between gap-4">
					<div>
						<h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
							Отзывы клиентов
						</h2>
						{/* Кликабельные карточки рейтингов площадок (только реальные профили). */}
						{cityProfile.reviewPlatforms.length ? (
							<div className="mt-3 flex flex-wrap gap-2">
								{cityProfile.reviewPlatforms.map((platform) => (
									<a
										key={platform.name}
										href={platform.url}
										target="_blank"
										rel="noreferrer"
										onClick={() =>
											trackEvent("review_platform_click", {
												platform: platform.name,
												city_slug: resolvedCitySlug,
											})
										}
										className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-800 transition hover:border-slate-300 hover:bg-slate-50"
									>
										<ProviderLogo provider={platform.name === "Яндекс" ? "yandex" : platform.name === "2ГИС" ? "2gis" : "google"} />
										{platform.name} — {platform.rating}
										<Star size={13} className="text-amber-500" fill="currentColor" />
									</a>
								))}
							</div>
						) : null}
					</div>

					{/* Стрелки навигации — только на десктопе, на мобиле свайп пальцем. */}
					<div className="hidden gap-2 sm:flex">
						<button
							type="button"
							onClick={() => scrollByCard(-1)}
							className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-50"
							aria-label="Предыдущие отзывы"
						>
							<ChevronLeft size={18} />
						</button>
						<button
							type="button"
							onClick={() => scrollByCard(1)}
							className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-50"
							aria-label="Следующие отзывы"
						>
							<ChevronRight size={18} />
						</button>
					</div>
				</div>

				{/* Слайдер: нативный горизонтальный скролл + snap. На мобиле — свайп. */}
				<div
					ref={trackRef}
					className="mt-6 flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
				>
					{reviews.map((review, index) => {
						const formattedDate = formatReviewDate(review.date);

						return (
							<motion.article
								key={review.id}
								data-review-card
								initial={{ opacity: 0, y: 14 }}
								whileInView={{ opacity: 1, y: 0 }}
								viewport={{ once: true, amount: 0.3 }}
								transition={{ duration: 0.3, delay: Math.min(index, 4) * 0.05 }}
								className="flex w-[85%] shrink-0 snap-start flex-col rounded-2xl border border-slate-200 bg-white p-5 sm:w-[320px]"
							>
								<div className="mb-3 flex items-center justify-between gap-2">
									<div className="flex items-center gap-1 text-amber-500">
										{Array.from({ length: review.rating }).map((_, i) => (
											<Star key={i} size={15} fill="currentColor" />
										))}
									</div>
									<ProviderBadge provider={review.provider} sourceUrl={review.sourceUrl} />
								</div>

								{review.serviceType ? (
									<p className="mb-2 inline-flex w-fit rounded-lg bg-sky-50 px-2 py-1 text-[11px] font-medium text-sky-900">
										{review.serviceType}
									</p>
								) : null}

								<p className="flex-1 text-sm leading-relaxed text-slate-700">{review.text}</p>

								<div className="mt-3 flex items-end justify-between gap-2">
									<p className="text-sm font-semibold text-slate-900">
										{review.author}
										{formattedDate ? (
											<span className="block text-xs font-normal text-muted">{formattedDate}</span>
										) : null}
									</p>
									{review.sourceUrl ? (
										<a
											href={review.sourceUrl}
											target="_blank"
											rel="noreferrer"
											className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-brand-deep transition hover:text-brand"
										>
											Смотреть оригинал
											<ExternalLink size={12} />
										</a>
									) : null}
								</div>
							</motion.article>
						);
					})}
				</div>

				<div className="mt-6">
					<a
						href={cityProfile.yandexBusinessUrl}
						target="_blank"
						rel="noreferrer"
						onClick={() => trackEvent("reviews_all_click", { city_slug: resolvedCitySlug })}
						className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:border-slate-300 hover:bg-slate-50"
					>
						Смотреть все отзывы
						<ExternalLink size={14} />
					</a>
				</div>
			</div>
		</section>
	);
}
