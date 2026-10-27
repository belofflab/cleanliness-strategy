"use client";

import { motion } from "framer-motion";
import { Baby, PackageCheck, ShieldAlert, Undo2 } from "lucide-react";

// «Безопасность и гарантия результата» (ТЗ п.9.2).
// Размещается сразу после блока преимуществ «Почему нам доверяют».
const SAFETY_CARDS = [
	{
		icon: PackageCheck,
		title: "Свои средства и оборудование",
		text: "Приезжаем с профессиональной химией и полным комплектом инвентаря. Вам не нужно ничего покупать или подготавливать.",
	},
	{
		icon: Baby,
		title: "Безопасность для детей и животных",
		text: "Работаем сертифицированными средствами, по запросу используем гипоаллергенную эко-линейку без резкого запаха. Дополнительная подготовка не нужна — достаточно предупредить о питомцах.",
	},
	{
		icon: ShieldAlert,
		title: "Ответственность за имущество",
		text: "До начала работ фиксируем состояние хрупких поверхностей и ведём фотофиксацию «до/после». Спорные ситуации разбираем с менеджером в течение одного рабочего дня.",
	},
	{
		icon: Undo2,
		title: "Исправление замечаний",
		text: "Если что-то упустили — бесплатно вернёмся и устраним недочёт в течение 24 часов после приёмки уборки.",
	},
];

export default function SafetySection() {
	return (
		<section id="safety" className="px-4 py-16 sm:px-6 lg:px-10">
			<div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
				<h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
					Безопасность и гарантия результата
				</h2>
				<p className="mt-2 max-w-3xl text-sm text-muted sm:text-base">
					Понятные правила работы: что мы привозим, чем убираем и как отвечаем за результат.
				</p>

				<div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					{SAFETY_CARDS.map((card, index) => {
						const Icon = card.icon;
						return (
							<motion.article
								key={card.title}
								initial={{ opacity: 0, y: 14 }}
								whileInView={{ opacity: 1, y: 0 }}
								viewport={{ once: true, amount: 0.3 }}
								transition={{ duration: 0.28, delay: index * 0.05 }}
								className="rounded-2xl border border-slate-200 bg-white p-5"
							>
								<span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
									<Icon size={18} />
								</span>
								<h3 className="mt-3 font-display text-base font-semibold text-slate-900">{card.title}</h3>
								<p className="mt-2 text-sm leading-relaxed text-muted">{card.text}</p>
							</motion.article>
						);
					})}
				</div>
			</div>
		</section>
	);
}
