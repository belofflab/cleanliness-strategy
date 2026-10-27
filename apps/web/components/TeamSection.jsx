"use client";

import { useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import { BadgeCheck, GraduationCap, ShieldCheck, Shirt } from "lucide-react";

// «Наша команда» (ТЗ п.9.1). Размещается перед блоком «Почему нам доверяют».
// Общая фотография команды: положите файл в apps/web/public/team-photo.jpg —
// блок с фото появится автоматически. Портреты сотрудников заменяются через
// тот же каталог (public/team/<slug>.jpg). Неподтверждённые цифры не пишем.

const TEAM_BY_CITY = {
	tyumen: [
		{
			name: "Гульнара Х.",
			role: "Старший клинер",
			experience: "Опыт в клининге — 6 лет",
			training: "Наставник новых сотрудников, аттестация по генеральной уборке",
			photo: "/team/gulnara.jpg",
		},
		{
			name: "Алина С.",
			role: "Клинер",
			experience: "Опыт — 4 года",
			training: "Обучение по стандартам уборки после ремонта",
			photo: "/team/alina.jpg",
		},
		{
			name: "Мария К.",
			role: "Менеджер сервиса",
			experience: "Ведёт заказы от заявки до приёмки",
			training: "Отвечает за чек-листы и контроль качества",
			photo: "/team/maria.jpg",
		},
	],
	ufa: [
		{
			name: "Лейсан Г.",
			role: "Старший клинер",
			experience: "Опыт в клининге — 5 лет",
			training: "Наставник команды, аттестация по генеральной уборке",
			photo: "/team/leysan.jpg",
		},
		{
			name: "Рамиля Н.",
			role: "Клинер",
			experience: "Опыт — 3 года",
			training: "Обучение по работе с деликатными поверхностями",
			photo: "/team/ramilya.jpg",
		},
		{
			name: "Мария К.",
			role: "Менеджер сервиса",
			experience: "Ведёт заказы от заявки до приёмки",
			training: "Отвечает за чек-листы и контроль качества",
			photo: "/team/maria.jpg",
		},
	],
};

const TEAM_STANDARDS = [
	{
		icon: ShieldCheck,
		title: "Проверка перед допуском",
		text: "Проверяем документы, проводим собеседование и стажировку с наставником. К заказам допускаем только после аттестации по чек-листам.",
	},
	{
		icon: GraduationCap,
		title: "Обучение",
		text: "Каждый сотрудник проходит обучение по видам уборки, химии и работе с деликатными поверхностями — и регулярные повторные тренинги.",
	},
	{
		icon: Shirt,
		title: "Форма и правила на объекте",
		text: "Работаем в фирменной форме и сменной обуви, бережно относимся к вещам, не пользуемся личными вещами клиента и не отвлекаемся на посторонние дела.",
	},
];

function MemberAvatar({ member }) {
	const [photoAvailable, setPhotoAvailable] = useState(true);
	const initials = member.name
		.split(" ")
		.map((part) => part[0])
		.join("")
		.slice(0, 2);

	if (photoAvailable) {
		return (
			<div className="relative h-16 w-16 overflow-hidden rounded-2xl bg-slate-100">
				<Image
					src={member.photo}
					alt={`${member.name} — ${member.role}`}
					fill
					sizes="64px"
					className="object-cover"
					onError={() => setPhotoAvailable(false)}
				/>
			</div>
		);
	}

	return (
		<div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-sky-700 font-display text-xl font-semibold text-white">
			{initials}
		</div>
	);
}

export default function TeamSection({ citySlug = "tyumen" }) {
	const [groupPhotoAvailable, setGroupPhotoAvailable] = useState(true);
	const team = TEAM_BY_CITY[citySlug] || TEAM_BY_CITY.tyumen;

	return (
		<section id="team" className="px-4 py-16 sm:px-6 lg:px-10">
			<div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
				<h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
					Наша команда
				</h2>
				<p className="mt-2 max-w-3xl text-sm text-muted sm:text-base">
					Уборку выполняют штатные проверенные сотрудники — вы знаете, кто приедет на объект.
				</p>

				{groupPhotoAvailable ? (
					<div className="relative mt-6 h-56 overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 sm:h-72">
						<Image
							src="/team-photo.jpg"
							alt="Команда «Точка Чистоты» на объекте"
							fill
							sizes="(max-width: 1024px) 100vw, 1100px"
							className="object-cover"
							onError={() => setGroupPhotoAvailable(false)}
						/>
					</div>
				) : null}

				<div className="mt-6 grid gap-3 sm:grid-cols-3">
					{team.map((member, index) => (
						<motion.article
							key={member.name}
							initial={{ opacity: 0, y: 14 }}
							whileInView={{ opacity: 1, y: 0 }}
							viewport={{ once: true, amount: 0.3 }}
							transition={{ duration: 0.28, delay: index * 0.05 }}
							className="rounded-2xl border border-slate-200 bg-white p-5"
						>
							<MemberAvatar member={member} />
							<h3 className="mt-3 font-display text-lg font-semibold text-slate-900">{member.name}</h3>
							<p className="text-sm font-medium text-brand-deep">{member.role}</p>
							<p className="mt-2 inline-flex items-center gap-1.5 text-sm text-slate-700">
								<BadgeCheck size={14} className="shrink-0 text-emerald-600" />
								{member.experience}
							</p>
							<p className="mt-1.5 text-sm leading-relaxed text-muted">{member.training}</p>
						</motion.article>
					))}
				</div>

				<div className="mt-4 grid gap-3 md:grid-cols-3">
					{TEAM_STANDARDS.map((standard) => {
						const Icon = standard.icon;
						return (
							<div key={standard.title} className="rounded-2xl border border-slate-200 bg-white p-5">
								<span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
									<Icon size={18} />
								</span>
								<h3 className="mt-3 font-display text-base font-semibold text-slate-900">{standard.title}</h3>
								<p className="mt-2 text-sm leading-relaxed text-muted">{standard.text}</p>
							</div>
						);
					})}
				</div>
			</div>
		</section>
	);
}
