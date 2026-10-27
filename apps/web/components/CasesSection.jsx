"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowRight, Clock3, MapPin, Ruler, SprayCan, Users } from "lucide-react";
import { api } from "@/lib/api";
import { normalizeCitySlug } from "@/lib/city";
import { trackEvent } from "@/lib/analytics";

// Кейсы «До/После» (ТЗ п.4 и п.9.3): минимум 4 реальных кейса, две фотографии
// с одного ракурса, под ними — параметры заказа и кнопка «Рассчитать похожую
// уборку». Фотографии публикуются с согласия клиентов; реальные снимки
// загружаются через админ-API (/admin/media/upload + /admin/before-after).
// Стоковые фотографии в этом блоке не используются.

const isRemote = (src) => /^https?:\/\//.test(src);

// Фоллбэк, если бэкенд недоступен: те же реальные кейсы, что и в сидах Уфы.
const DEFAULT_CASES = [
	{
		id: "demo-1",
		title: "Уборка сильно запущенной комнаты",
		before_url: "/cases/room-deep-before.webp",
		after_url: "/cases/room-deep-after.webp",
		room_type: "Комната в квартире",
		area_sqm: 17,
		cleaning_type: "Генеральная уборка",
		cleaners_count: 2,
		duration_hours: 6,
		cost_text: "9 400 ₽",
		district: "Проспект Октября",
		task_text: "Комната после длительного проживания: завалы вещей, пыль, загрязнённые поверхности.",
		review_text: "Не верили, что комнату можно вернуть в такое состояние. Спасибо!",
	},
	{
		id: "demo-2",
		title: "Генеральная уборка ванной комнаты",
		before_url: "/cases/bathroom-before.webp",
		after_url: "/cases/bathroom-after.webp",
		room_type: "Ванная комната",
		area_sqm: 5,
		cleaning_type: "Генеральная уборка",
		cleaners_count: 1,
		duration_hours: 3,
		cost_text: "3 800 ₽",
		district: "Сипайлово",
		task_text: "Известковый налёт на сантехнике и плитке, швы, зеркала и стеклянные поверхности.",
		review_text: "Сантехника блестит, швы как новые — очень довольны.",
	},
	{
		id: "demo-3",
		title: "Поддерживающая уборка кухни",
		before_url: "/cases/kitchen-dishes-before.webp",
		after_url: "/cases/kitchen-dishes-after.webp",
		room_type: "Кухня",
		area_sqm: 10,
		cleaning_type: "Поддерживающая уборка",
		cleaners_count: 1,
		duration_hours: 2,
		cost_text: "2 700 ₽",
		district: "Зелёная Роща",
		task_text: "Посуда, рабочие поверхности, плита и раковина после насыщенной недели.",
		review_text: "Удобно заказывать регулярно — кухня всегда в порядке.",
	},
	{
		id: "demo-4",
		title: "Генеральная уборка кухни",
		before_url: "/cases/kitchen-gas-before.webp",
		after_url: "/cases/kitchen-gas-after.webp",
		room_type: "Кухня",
		area_sqm: 8,
		cleaning_type: "Генеральная уборка",
		cleaners_count: 1,
		duration_hours: 3,
		cost_text: "4 200 ₽",
		district: "Черниковка",
		task_text: "Жир на плите и фартуке, фасады, раковина и смеситель.",
		review_text: "Отмыли даже то, что мы считали безнадёжным.",
	},
];

function formatDuration(hours) {
	if (!hours) return null;
	const whole = Math.floor(hours);
	const minutes = Math.round((hours - whole) * 60);
	if (!whole) return `${minutes} мин`;
	return minutes ? `${whole} ч ${minutes} мин` : `${whole} ч`;
}

// Интерактивное сравнение «До/После»: перетаскиваемая граница между снимками.
function BeforeAfterViewer({ beforeUrl, afterUrl, title }) {
	const containerRef = useRef(null);
	const overlayRef = useRef(null);
	const handleRef = useRef(null);
	const positionRef = useRef(55);
	const rafRef = useRef(0);
	const draggingRef = useRef(false);
	const [dragging, setDragging] = useState(false);

	const applyPosition = useCallback((value) => {
		const clamped = Math.min(100, Math.max(0, value));
		positionRef.current = clamped;
		if (overlayRef.current) {
			overlayRef.current.style.clipPath = `inset(0 ${100 - clamped}% 0 0)`;
		}
		if (handleRef.current) {
			handleRef.current.style.left = `${clamped}%`;
		}
	}, []);

	const scheduleFromClientX = useCallback(
		(clientX) => {
			if (rafRef.current) return;
			rafRef.current = requestAnimationFrame(() => {
				rafRef.current = 0;
				const rect = containerRef.current?.getBoundingClientRect();
				if (!rect) return;
				applyPosition(((clientX - rect.left) / rect.width) * 100);
			});
		},
		[applyPosition],
	);

	useEffect(() => {
		applyPosition(positionRef.current);
		return () => {
			if (rafRef.current) cancelAnimationFrame(rafRef.current);
		};
	}, [applyPosition]);

	const handlePointerDown = (event) => {
		draggingRef.current = true;
		setDragging(true);
		event.currentTarget.setPointerCapture?.(event.pointerId);
		scheduleFromClientX(event.clientX);
	};

	const handlePointerMove = (event) => {
		if (!draggingRef.current) return;
		scheduleFromClientX(event.clientX);
	};

	const handlePointerUp = (event) => {
		draggingRef.current = false;
		setDragging(false);
		event.currentTarget.releasePointerCapture?.(event.pointerId);
	};

	return (
		<div
			ref={containerRef}
			className="relative h-[220px] touch-none select-none overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:h-[260px]"
			onPointerDown={handlePointerDown}
			onPointerMove={handlePointerMove}
			onPointerUp={handlePointerUp}
			onPointerCancel={handlePointerUp}
			role="presentation"
		>
			{/* Хронология слева направо: «До» — слева (оверлей), «После» — справа (базовый слой). */}
			<Image
				src={afterUrl}
				alt={`После уборки — ${title || "кейс"}`}
				fill
				className="object-cover"
				sizes="(max-width: 1024px) 100vw, 560px"
				unoptimized={isRemote(afterUrl)}
			/>

			<div
				ref={overlayRef}
				className="pointer-events-none absolute inset-0 will-change-[clip-path]"
				style={{ clipPath: "inset(0 45% 0 0)" }}
			>
				<Image
					src={beforeUrl}
					alt={`До уборки — ${title || "кейс"}`}
					fill
					className="object-cover"
					sizes="(max-width: 1024px) 100vw, 560px"
					unoptimized={isRemote(beforeUrl)}
				/>
			</div>

			<div ref={handleRef} className="pointer-events-none absolute inset-y-0 will-change-[left]" style={{ left: "55%" }}>
				<div className="h-full w-0.5 -translate-x-1/2 bg-white/90 shadow-lg shadow-slate-900/30" />
				<div
					className={`absolute left-1/2 top-1/2 flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/70 bg-white/95 text-xs font-semibold text-slate-800 shadow-lg transition-transform duration-150 ${
						dragging ? "scale-110" : "scale-100"
					}`}
				>
					↔
				</div>
			</div>

			<span className="absolute left-3 top-3 rounded-lg bg-black/50 px-2 py-1 text-xs font-medium text-white">До</span>
			<span className="absolute right-3 top-3 rounded-lg bg-white/80 px-2 py-1 text-xs font-medium text-slate-900">После</span>
		</div>
	);
}

function CaseMetaChip({ icon: Icon, children }) {
	return (
		<span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
			<Icon size={12} className="text-slate-500" />
			{children}
		</span>
	);
}

export default function CasesSection({ citySlug }) {
	const resolvedCitySlug = normalizeCitySlug(citySlug);
	const [cases, setCases] = useState(DEFAULT_CASES);

	useEffect(() => {
		const controller = new AbortController();

		api
			.getBeforeAfter(resolvedCitySlug, controller.signal)
			.then((data) => {
				if (Array.isArray(data) && data.length > 0) {
					setCases(data);
				}
				// Нет данных — остаёмся на структурных плейсхолдерах.
			})
			.catch(() => {
				// API недоступен — молча используем дефолтные кейсы.
			});

		return () => controller.abort();
	}, [resolvedCitySlug]);

	const handleCaseCta = (item) => {
		trackEvent("case_cta_click", {
			case_title: item.title,
			cleaning_type: item.cleaning_type,
			city_slug: resolvedCitySlug,
		});
	};

	return (
		<section id="before-after" className="px-4 py-16 sm:px-6 lg:px-10">
			<div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
				<h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
					Реальные кейсы: до и после
				</h2>
				<p className="mt-2 max-w-3xl text-sm text-muted sm:text-base">
					Две фотографии с одного ракурса, параметры заказа и стоимость. Фотографии
					публикуем с согласия клиентов — без документов, людей и личных вещей в кадре.
				</p>

				<div className="mt-6 grid gap-4 lg:grid-cols-2">
					{cases.map((item, index) => (
						<motion.article
							key={item.id}
							initial={{ opacity: 0, y: 16 }}
							whileInView={{ opacity: 1, y: 0 }}
							viewport={{ once: true, amount: 0.15 }}
							transition={{ duration: 0.3, delay: Math.min(index, 3) * 0.06 }}
							className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 sm:p-5"
						>
							<BeforeAfterViewer beforeUrl={item.before_url} afterUrl={item.after_url} title={item.title} />

							<h3 className="mt-4 font-display text-lg font-semibold text-slate-900">{item.title}</h3>

							<div className="mt-3 flex flex-wrap gap-1.5">
								{item.room_type ? <CaseMetaChip icon={MapPin}>{item.room_type}</CaseMetaChip> : null}
								{item.area_sqm ? <CaseMetaChip icon={Ruler}>{item.area_sqm} м²</CaseMetaChip> : null}
								{item.cleaning_type ? <CaseMetaChip icon={SprayCan}>{item.cleaning_type}</CaseMetaChip> : null}
								{item.cleaners_count ? (
									<CaseMetaChip icon={Users}>
										{item.cleaners_count} {item.cleaners_count === 1 ? "специалист" : "специалиста"}
									</CaseMetaChip>
								) : null}
								{item.duration_hours ? <CaseMetaChip icon={Clock3}>{formatDuration(item.duration_hours)}</CaseMetaChip> : null}
								{item.district ? <CaseMetaChip icon={MapPin}>{item.district}</CaseMetaChip> : null}
							</div>

							{item.task_text ? (
								<p className="mt-3 text-sm leading-relaxed text-slate-700">
									<span className="font-semibold text-slate-900">Задача: </span>
									{item.task_text}
								</p>
							) : null}

							{item.review_text ? (
								<p className="mt-2 rounded-xl bg-sky-50 px-3 py-2 text-sm italic leading-relaxed text-sky-950">
									«{item.review_text}»
								</p>
							) : null}

							<div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
								{item.cost_text ? (
									<p className="font-display text-xl font-semibold text-slate-950">{item.cost_text}</p>
								) : (
									<span />
								)}
								<a
									href="#calculator"
									onClick={() => handleCaseCta(item)}
									className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
								>
									Рассчитать похожую уборку
									<ArrowRight size={14} />
								</a>
							</div>
						</motion.article>
					))}
				</div>
			</div>
		</section>
	);
}
