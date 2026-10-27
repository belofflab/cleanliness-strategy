"use client";

import { motion } from "framer-motion";
import { AlertTriangle, DoorOpen, FileLock2, Key, PawPrint, Plug } from "lucide-react";

// «Подготовка к приезду клинеров» (ТЗ п.9.4). Размещается перед FAQ:
// снимает тревогу и уменьшает количество уточняющих звонков.
const PREPARATION_ITEMS = [
	{
		icon: FileLock2,
		title: "Уберите документы и ценные вещи",
		text: "Деньги, документы и украшения лучше убрать заранее — мы не перемещаем личные вещи без согласования.",
	},
	{
		icon: AlertTriangle,
		title: "Предупредите о хрупких поверхностях",
		text: "Расскажите менеджеру о деликатных материалах и предметах, которые требуют особой аккуратности.",
	},
	{
		icon: Plug,
		title: "Обеспечьте воду и электричество",
		text: "Для работы оборудования нужны рабочие розетки и доступ к воде — проверьте их заранее.",
	},
	{
		icon: PawPrint,
		title: "Сообщите о животных",
		text: "Предупредите о питомцах: подберём средства и договоримся, где животному будет спокойнее во время уборки.",
	},
	{
		icon: DoorOpen,
		title: "Освободите доступ к нужным зонам",
		text: "Откройте комнаты и зоны, которые нужно убрать, — так команда сразу приступит к работе.",
	},
	{
		icon: Key,
		title: "Можно передать ключи и отсутствовать",
		text: "Многие клиенты передают ключи и занимаются своими делами: пришлём фотоотчёт и согласуем приёмку по возвращении.",
	},
];

export default function PreparationSection() {
	return (
		<section id="preparation" className="px-4 py-16 sm:px-6 lg:px-10">
			<div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
				<h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
					Подготовка к приезду клинеров
				</h2>
				<p className="mt-2 max-w-3xl text-sm text-muted sm:text-base">
					Несколько простых шагов перед уборкой — и команда сразу приступит к делу.
				</p>

				<div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					{PREPARATION_ITEMS.map((item, index) => {
						const Icon = item.icon;
						return (
							<motion.article
								key={item.title}
								initial={{ opacity: 0, y: 14 }}
								whileInView={{ opacity: 1, y: 0 }}
								viewport={{ once: true, amount: 0.3 }}
								transition={{ duration: 0.28, delay: index * 0.04 }}
								className="rounded-2xl border border-slate-200 bg-white p-5"
							>
								<span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
									<Icon size={18} />
								</span>
								<h3 className="mt-3 font-display text-base font-semibold text-slate-900">{item.title}</h3>
								<p className="mt-2 text-sm leading-relaxed text-muted">{item.text}</p>
							</motion.article>
						);
					})}
				</div>
			</div>
		</section>
	);
}
