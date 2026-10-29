"""Целевой сценарий «500»: что нужно, чтобы Тюмень приносила 500 тыс. ₽ операционной прибыли в месяц.

    cd strategy/model && python3 target_500.py      → target_500.md

Та же модель (model.py), что и у трёх сценариев. Реалистичный сценарий меняется по пяти рычагам из блока 7
плана (strategy/PLAYBOOK.md). Прибыль здесь — после налогов (УСН, НДС при превышении порога), маркетинга и FIX,
до CAPEX второго этапа и до выплат собственнику.
"""

from __future__ import annotations

import copy
import os

import assumptions as A
import model as M

TARGET = 500_000
# Рычаги целевого плана поверх реалистичного сценария: (ключ, значение, как достигается)
LEVERS = [
    ("a_m6", 60, "60 заказов A в месяц к апрелю 2027 (в реалистичном 45): партнёры-бригады и ЖК, Авито, страницы ЖК"),
    ("a_growth", 0.05, "Рост A 5% в месяц после M6 (в реалистичном 4%)"),
    ("a_cap", 140, "Потолок мощности 140 заказов A: третья и четвёртая бригады к осени 2027"),
    ("s_m6", 20, "20 новых подписчиков в месяц к апрелю (в реалистичном 14): предложение подписки после каждой уборки"),
    ("churn", 0.07, "Отток подписки 7% в месяц (в реалистичном 9%): закреплённый клинер, перенос без звонка"),
    ("spec_ratio", 0.6, "Химчистка и окна в 60% заказов A (в реалистичном 45%): допродажа скриптом и в подтверждении"),
    ("b2b_start", 3, "Первый B2B-договор в январе 2027"),
    ("b2b_step", 2, "Новый B2B-договор каждые 2 месяца"),
    ("b2b_max", 8, "До 8 B2B-договоров"),
]
SINGLE = [  # по одному рычагу — чтобы видеть вклад каждого
    ("Больше заказов A (60 к M6, рост 5%)", {"a_m6": 60, "a_growth": 0.05, "a_cap": 140}),
    ("Подписка: приток 20 в месяц к M6", {"s_m6": 20}),
    ("Подписка: отток 7%", {"churn": 0.07}),
    ("Допродажи химчистки и окон 60%", {"spec_ratio": 0.6}),
    ("B2B: с января, раз в 2 месяца, до 8", {"b2b_start": 3, "b2b_step": 2, "b2b_max": 8}),
]
MONTHS = ("янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек")


def run_with(over: dict, code: str = "R"):
    saved = copy.deepcopy(A.SCENARIOS)
    i = A.SCENARIO_CODES.index(code)
    try:
        for k, val in over.items():
            t = list(A.SCENARIOS[k])
            t[1 + i] = val
            A.SCENARIOS[k] = tuple(t)
        return M.run(code)
    finally:
        A.SCENARIOS = saved


def first_month(rows, value):
    return next((r["m"] for r in rows if r["profit"] >= value), None)


def fmt(x):
    return f"{x:,.0f}".replace(",", " ")


def month_name(r):
    return f"{MONTHS[r['month'] - 1]} {r['year']}"


def build():
    base = run_with({})
    target = run_with({k: v for k, v, _ in LEVERS})
    lead_conv = M.v(A.TARGETS, "lead_to_order_a")
    trial_conv = M.v(A.TARGETS, "trial_to_sub")
    out = ["# Целевой сценарий «500» (сгенерировано target_500.py)", "",
           "Не редактируйте вручную: файл пересобирается из `model/target_500.py`. Прибыль — после УСН, НДС,",
           "маркетинга и FIX, до CAPEX второго этапа и выплат собственнику.", "",
           "## Рычаги поверх реалистичного сценария", ""]
    out += [f"- **{k} = {v}** — {why}" for k, v, why in LEVERS]
    out += ["", "## Вклад рычагов по отдельности", "",
            "| Рычаг | Прибыль M12, ₽ | Прирост к реалистичному, ₽ | Первый месяц ≥ 500 тыс. |", "|---|---:|---:|---|"]
    b12 = base[11]["profit"]
    out.append(f"| Реалистичный сценарий | {fmt(b12)} | — | M{first_month(base, TARGET)} |")
    for name, over in SINGLE:
        rows = run_with(over)
        out.append(f"| {name} | {fmt(rows[11]['profit'])} | +{fmt(rows[11]['profit'] - b12)} | M{first_month(rows, TARGET)} |")
    out.append(f"| **Все рычаги вместе** | **{fmt(target[11]['profit'])}** | **+{fmt(target[11]['profit'] - b12)}** | "
               f"**M{first_month(target, TARGET)}** |")
    out += ["", "## Помесячно: целевой план против реалистичного", "",
            "Лиды A — заявки на генеральную и после ремонта при конверсии "
            f"{lead_conv:.0%}. Пробные уборки — разовые поддерживающие, из которых {trial_conv:.0%} переходят в подписку.", "",
            "| M | Месяц | Заказы A | Лидов A в день | Пробных уборок | Новые подписчики | Активные подписчики | Химчистка и окна | B2B | "
            "Выручка, ₽ | Маркетинг, ₽ | FIX, ₽ | НДС, ₽ | Прибыль, ₽ | Прибыль реалист., ₽ | Клинеров (FTE) |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r, rb in zip(target, base):
        out.append(f"| {r['m']} | {month_name(r)} | {r['a']:.0f} | {r['a'] / lead_conv / 30:.1f} | {r['new_subs'] / trial_conv:.0f} | "
                   f"{r['new_subs']:.0f} | {r['active']:.0f} | {r['spec']:.0f} | {r['contracts']} | {fmt(r['rev'])} | {fmt(r['mkt'])} | "
                   f"{fmt(r['fix'])} | {fmt(r['vat'])} | **{fmt(r['profit'])}** | {fmt(rb['profit'])} | {r['fte']:.1f} |")
    vat_m = next((r for r in target if r["vat_on"]), None)
    sustained = next((r["m"] for r in target if all(x["profit"] >= TARGET for x in target if x["m"] >= r["m"])), None)
    capex0 = M.capex_total(A.CAPEX_ITEMS) + M.prelaunch_total()
    cum, worst, payback = -capex0, -capex0, None
    for r in target:
        cum += r["cf"]
        worst = min(worst, cum)
        if payback is None and cum >= 0:
            payback = r["m"]
    out += ["", "## Итоги", "",
            f"- Первый месяц с прибылью ≥ 500 тыс. ₽: **M{first_month(target, TARGET)}** "
            f"({month_name(target[first_month(target, TARGET) - 1])}); в реалистичном сценарии — M{first_month(base, TARGET)}.",
            f"- Прибыль ≥ 500 тыс. ₽ каждый месяц до конца горизонта: с M{sustained}." if sustained else
            "- Прибыль проседает ниже 500 тыс. ₽ в отдельные месяцы (январь и включение НДС) — см. таблицу.",
            f"- НДС 5% включается в M{vat_m['m']} ({month_name(vat_m)}), когда выручка за год превышает 20 млн ₽. "
            "Порог считается по юрлицу, то есть вместе с Уфой: с уфимской выручкой НДС придёт раньше." if vat_m else "- НДС за горизонт не включается.",
            f"- Выручка за 12 месяцев: {fmt(sum(r['rev'] for r in target[:12]))} ₽; прибыль за 12 месяцев: "
            f"{fmt(sum(r['profit'] for r in target[:12]))} ₽.",
            f"- Худшая точка накопленного денежного потока (с CAPEX и предзапуском): {fmt(worst)} ₽; окупаемость — M{payback}.",
            f"- Клинеров к M12: ≈ {target[11]['fte']:.0f} FTE против ≈ {base[11]['fte']:.0f} в реалистичном сценарии.", ""]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target_500.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"→ {path}")
    return target, base


if __name__ == "__main__":
    build()
