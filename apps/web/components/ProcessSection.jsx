"use client";

import { motion } from "framer-motion";
import { CalendarCheck2, House, Sparkles, WalletCards } from "lucide-react";

const STEPS = [
  {
    title: "1. Вы оставляете заявку",
    description: "Через сайт, Telegram, Max или звонок. Отвечаем в течение 7 минут.",
    icon: CalendarCheck2,
  },
  {
    title: "2. Согласуем детали",
    description: "Уточняем тип уборки, площадь и доп-услуги. Фиксируем финальную цену.",
    icon: WalletCards,
  },
  {
    title: "3. Проводим уборку",
    description: "Команда приезжает в согласованное время со своим инвентарем и химией.",
    icon: House,
  },
  {
    title: "4. Принимаете результат",
    description: "Проверка по чек-листу и финальная приемка. Оплата после завершения.",
    icon: Sparkles,
  },
];

export default function ProcessSection() {
  return (
    <section id="process" className="px-4 py-16 sm:px-6 lg:px-10">
      <div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
        <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Как проходит заказ
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-muted sm:text-base">
          От заявки до готового результата — четыре понятных шага. Стоимость и время уборки
          согласуем заранее.
        </p>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {STEPS.map((step, index) => {
            const Icon = step.icon;

            return (
              <motion.article
                key={step.title}
                initial={{ opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.28, delay: index * 0.05 }}
                className="rounded-2xl border border-slate-200 bg-white p-5"
              >
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                  <Icon size={18} />
                </span>
                <h3 className="mt-3 font-display text-lg font-semibold text-slate-900">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{step.description}</p>
              </motion.article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

