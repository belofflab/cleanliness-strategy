"""Сборка Excel-финмодели cleanliness.pro с живыми формулами.

    python3 build_finmodel.py              # собрать cleanliness_finmodel.xlsx + model_output.md
    python3 build_finmodel.py --verify     # то же + сверить пересчитанный Excel с Python-моделью

Все числа берутся из assumptions.py. Входные ячейки — синим шрифтом,
ключевые допущения — с жёлтой заливкой, формулы — чёрным,
ссылки на другие листы — зелёным.
"""

import json
import os
import subprocess
import sys

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

import assumptions as A
import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, "cleanliness_finmodel.xlsx")
MD = os.path.join(HERE, "model_output.md")

FONT = "Arial"
F_IN = Font(name=FONT, color="0000FF")
F_CALC = Font(name=FONT, color="000000")
F_LINK = Font(name=FONT, color="008000")
F_BOLD = Font(name=FONT, bold=True)
F_TITLE = Font(name=FONT, bold=True, size=14)
F_HEAD = Font(name=FONT, bold=True, color="FFFFFF")
F_NOTE = Font(name=FONT, italic=True, color="666666", size=9)
FILL_KEY = PatternFill("solid", fgColor="FFFF00")
FILL_HEAD = PatternFill("solid", fgColor="1F4E78")
FILL_SEC = PatternFill("solid", fgColor="DDEBF7")
FILL_TOTAL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(top=THIN, bottom=THIN)

RUB = '#,##0;(#,##0);"-"'
RUB1 = '#,##0.0;(#,##0.0);"-"'
PCT = '0.0%;(0.0%);"-"'
NUM1 = '0.0;(0.0);"-"'
NUM2 = '0.00'

SCN_SHEETS = {"P": "ОПиУ_Пессимист", "R": "ОПиУ_Реалист", "O": "ОПиУ_Оптимист"}
MONTH_NAMES = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def q(sheet):
    return f"'{sheet}'"


class Book:
    def __init__(self):
        self.wb = Workbook()
        self.wb.remove(self.wb.active)

    def name(self, nm, sheet, cell):
        col = "".join(ch for ch in cell if ch.isalpha())
        row = "".join(ch for ch in cell if ch.isdigit())
        dn = DefinedName(nm, attr_text=f"{q(sheet)}!${col}${row}")
        self.wb.defined_names[nm] = dn

    def name_range(self, nm, sheet, rng):
        a, b = rng.split(":")
        ca = "".join(ch for ch in a if ch.isalpha()); ra = "".join(ch for ch in a if ch.isdigit())
        cb = "".join(ch for ch in b if ch.isalpha()); rb = "".join(ch for ch in b if ch.isdigit())
        self.wb.defined_names[nm] = DefinedName(nm, attr_text=f"{q(sheet)}!${ca}${ra}:${cb}${rb}")


def style_cell(c, font=F_CALC, fmt=None, fill=None, bold=False):
    c.font = Font(name=FONT, color=font.color, bold=bold or font.bold, italic=font.italic, size=font.size)
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill


def header_row(ws, row, values, start_col=1):
    for i, val in enumerate(values):
        c = ws.cell(row=row, column=start_col + i, value=val)
        c.font = F_HEAD
        c.fill = FILL_HEAD
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def section(ws, row, title, width=4):
    for col in range(1, width + 1):
        ws.cell(row=row, column=col).fill = FILL_SEC
    c = ws.cell(row=row, column=1, value=title)
    c.font = F_BOLD


# ---------------------------------------------------------------- Инструкция

def sheet_readme(book):
    ws = book.wb.create_sheet("Инструкция")
    ws["A1"] = "Финансовая модель запуска «Точки Чистоты» (cleanliness.pro) в Тюмени"
    ws["A1"].font = F_TITLE
    lines = [
        "Горизонт: 24 месяца, M1 = ноябрь 2026. Суммы в рублях.",
        "",
        "Как пользоваться:",
        "1. Меняйте только ячейки с СИНИМ шрифтом на листах «Допущения» и «Сценарии».",
        "   Жёлтая заливка — ключевые допущения, сильнее всего влияющие на результат.",
        "2. Листы «Юнит-экономика», «ОПиУ_*» и «Сводка» считаются формулами автоматически.",
        "3. Сценарии отличаются только объёмами, оттоком и CAC (лист «Сценарии»); цены и затраты на заказ общие.",
        "4. Модель считается на РЕКОМЕНДУЕМОМ прайсе. Прежний прайс сайта (сиды до обновления) — для сравнения на листе «Юнит-экономика».",
        "",
        "Цветовая легенда:",
        "   синий шрифт — ввод; чёрный — формула; зелёный — ссылка на другой лист; жёлтая заливка — ключевое допущение.",
        "",
        "Логика ОПиУ (по месяцам):",
        "   Выручка = заказы A × чек A + визиты B × цена визита + спецуслуги × чек S + B2B-договоры × сумма договора",
        "   Операционная прибыль = Выручка − НДС − переменные затраты − маркетинг (CAC) − FIX − УСН",
        "   FIX растёт ступенькой: + «доп. накладные» на каждые «ступень выручки» в месяц.",
        "   НДС 5% включается, если выручка прошлого года > 20 млн ₽ или накопленная выручка текущего года превысила 20 млн ₽.",
        "   Подписчики: активные(m) = активные(m−1) × (1 − отток) + новые(m).",
        "",
        "Ограничения: модель не учитывает вознаграждение собственника, дебиторку B2B (отсрочка 15–30 дней —",
        "закрывается резервом), инфляцию цен и ФОТ. Цифры рынка — ориентиры по открытым источникам (см. «Допущения»).",
        "",
        "Источник цифр: strategy/model/assumptions.py. Сборка: python3 strategy/model/build_finmodel.py",
    ]
    for i, t in enumerate(lines, start=3):
        ws.cell(row=i, column=1, value=t).font = Font(name=FONT)
    ws.column_dimensions["A"].width = 120


# ---------------------------------------------------------------- Допущения

def sheet_assumptions(book):
    ws = book.wb.create_sheet("Допущения")
    sh = ws.title
    ws["A1"] = "Допущения модели"
    ws["A1"].font = F_TITLE
    header_row(ws, 3, ["Параметр", "Значение", "Ед.", "Источник / комментарий"])
    r = 4
    key_inputs = {"UA_price_general_m2", "UA_price_repair_m2", "UA_labor_share", "UB_price_single",
                  "UB_labor_share", "UB_visits_per_month", "fix_step_cost"}

    def put(name, label, val, unit, note, fmt):
        nonlocal r
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        c = ws.cell(row=r, column=2, value=val)
        style_cell(c, F_IN, fmt, FILL_KEY if name in key_inputs else None)
        ws.cell(row=r, column=3, value=unit).font = Font(name=FONT)
        ws.cell(row=r, column=4, value=note).font = F_NOTE
        book.name(name, sh, f"B{r}")
        r += 1

    def fmt_for(key, val):
        if isinstance(val, float) and val < 1 and key not in ("visits_per_month",):
            return PCT
        if isinstance(val, float):
            return NUM1
        return RUB

    section(ws, r, "Календарь"); r += 1
    put("start_year", "Год начала (M1)", A.START_YEAR, "год", "M1 = ноябрь 2026", "0")
    put("start_month", "Месяц начала (M1)", A.START_MONTH, "мес", "", "0")

    section(ws, r, "Налоги и платежи"); r += 1
    units = {"usn_rate": "%", "vat_threshold": "₽/год", "vat_rate": "%", "acquiring": "% чека"}
    for k, (val, note) in A.TAX.items():
        put(k, {"usn_rate": "Ставка УСН «доходы»", "vat_threshold": "Порог освобождения от НДС",
                "vat_rate": "Ставка НДС для УСН сверх порога", "acquiring": "Эквайринг / СБП"}[k],
            val, units[k], note, PCT if k != "vat_threshold" else RUB)

    labels_a = {"area": ("Площадь типового объекта", "м²"), "price_general_m2": ("Цена генеральной", "₽/м²"),
                "price_repair_m2": ("Цена уборки после ремонта", "₽/м²"),
                "share_repair": ("Доля «после ремонта» в типе A", "%"), "upsell": ("Средний допчек", "₽"),
                "man_hours": ("Трудоёмкость заказа", "чел-ч"), "labor_share": ("Оплата клинеров", "% чека"),
                "chem": ("Химия и расходники", "₽/заказ"), "amort": ("Амортизация оборудования", "₽/заказ"),
                "logistics": ("Логистика", "₽/заказ"), "quality_reserve": ("Резерв качества", "% чека")}
    section(ws, r, "Юнит A — генеральная / после ремонта"); r += 1
    for k, (val, note) in A.UNIT_A.items():
        put(f"UA_{k}", labels_a[k][0], val, labels_a[k][1], note, fmt_for(k, val))

    labels_b = {"area": ("Площадь типового объекта", "м²"), "price_single": ("Цена разовой поддерживающей", "₽"),
                "sub_discount": ("Средняя скидка подписки", "%"), "hours": ("Длительность визита", "ч"),
                "labor_share": ("Оплата клинера", "% чека"), "chem": ("Химия и расходники", "₽/визит"),
                "amort": ("Амортизация инвентаря", "₽/визит"), "logistics": ("Проезд клинера", "₽/визит"),
                "quality_reserve": ("Резерв качества", "% чека"),
                "visits_per_month": ("Визитов на подписчика в месяц", "визитов")}
    section(ws, r, "Юнит B — поддерживающая (подписка)"); r += 1
    for k, (val, note) in A.UNIT_B.items():
        put(f"UB_{k}", labels_b[k][0], val, labels_b[k][1], note, fmt_for(k, val))

    labels_s = {"aov": ("Средний чек спецуслуги", "₽"), "man_hours": ("Трудоёмкость", "чел-ч"),
                "labor_share": ("Оплата мастера", "% чека"), "chem": ("Химия", "₽/заказ"),
                "amort": ("Амортизация", "₽/заказ"), "logistics": ("Логистика", "₽/заказ"),
                "quality_reserve": ("Резерв качества", "% чека")}
    section(ws, r, "Юнит S — спецуслуги (химчистка мебели, окна)"); r += 1
    for k, (val, note) in A.UNIT_S.items():
        put(f"US_{k}", labels_s[k][0], val, labels_s[k][1], note, fmt_for(k, val))

    section(ws, r, "B2B — обслуживание офисов по договору"); r += 1
    put("b2b_value", "Сумма договора", A.B2B["contract_value"][0], "₽/мес", A.B2B["contract_value"][1], RUB)
    put("b2b_direct_share", "Прямые затраты", A.B2B["direct_share"][0], "% выручки", A.B2B["direct_share"][1], PCT)

    section(ws, r, "Прежний прайс Тюмени (seed.py на ревизии 0be802d) — для сравнения"); r += 1
    put("cur_rooms", "Типовой объект: комнат", A.CURRENT_OBJECT["rooms"], "шт", "Тариф = база + комнаты × ставка + санузлы × ставка", "0")
    put("cur_baths", "Типовой объект: санузлов", A.CURRENT_OBJECT["bathrooms"], "шт", "", "0")
    tnames = {"maintenance": ("maint", "Поддерживающая"), "general": ("gen", "Генеральная"),
              "post_renovation": ("post", "После ремонта")}
    for t, (base, room, bath, mb, mr, mbath) in A.CURRENT_TARIFFS.items():
        code, label = tnames[t]
        put(f"cur_{code}_base", f"{label}: база", base, "₽", "Сиды проекта до обновления, город tyumen", RUB)
        put(f"cur_{code}_room", f"{label}: за комнату", room, "₽", "", RUB)
        put(f"cur_{code}_bath", f"{label}: за санузел", bath, "₽", "", RUB)
        put(f"cur_{code}_min", f"{label}: норма времени на объект", mb + A.CURRENT_OBJECT["rooms"] * mr + A.CURRENT_OBJECT["bathrooms"] * mbath, "мин", "minutes_base + комнаты × мин + санузлы × мин (из сидов)", "0")

    section(ws, r, "Персонал и целевые ориентиры"); r += 1
    put("hours_per_fte", "Продуктивных часов клинера в месяц", A.STAFF["hours_per_fte"][0], "ч", A.STAFF["hours_per_fte"][1], "0")
    put("b2b_fte", "Клинеров на 1 B2B-договор", A.STAFF["b2b_fte"][0], "FTE", A.STAFF["b2b_fte"][1], "0")
    tl = {"target_margin_a": ("Целевая маржа заказа A после CAC", "% чека"),
          "ltv_cac_min": ("Минимальный LTV / CAC", "x"),
          "payback_months_b": ("Макс. окупаемость CAC подписчика", "мес"),
          "lead_to_order_a": ("Конверсия лида в заказ A", "%"),
          "trial_to_sub": ("Конверсия пробной уборки в подписку", "%")}
    for k, (val, note) in A.TARGETS.items():
        put(k, tl[k][0], val, tl[k][1], note, PCT if isinstance(val, float) else "0")

    section(ws, r, "Сезонность разовых заказов (индекс по календарному месяцу)"); r += 1
    s0 = r
    for mth in range(1, 13):
        ws.cell(row=r, column=1, value=f"{mth:02d} — {MONTH_NAMES[mth - 1]}").font = Font(name=FONT)
        c = ws.cell(row=r, column=2, value=A.SEASONALITY[mth])
        style_cell(c, F_IN, NUM2)
        ws.cell(row=r, column=3, value="индекс").font = Font(name=FONT)
        if mth == 1:
            ws.cell(row=r, column=4, value="Экспертная оценка для Тюмени: провал янв–фев, пики апр–май, авг–сен, дек").font = F_NOTE
        r += 1
    book.name_range("season_tbl", sh, f"B{s0}:B{r - 1}")

    section(ws, r, "Постоянные расходы (FIX), ₽/мес"); r += 1
    f0 = r
    for label, val in A.FIX_ITEMS:
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        style_cell(ws.cell(row=r, column=2, value=val), F_IN, RUB)
        ws.cell(row=r, column=3, value="₽/мес").font = Font(name=FONT)
        r += 1
    ws.cell(row=r, column=1, value="FIX базовый, итого").font = F_BOLD
    c = ws.cell(row=r, column=2, value=f"=SUM(B{f0}:B{r - 1})")
    style_cell(c, F_CALC, RUB, FILL_TOTAL, bold=True)
    ws.cell(row=r, column=4, value="Без вознаграждения собственника").font = F_NOTE
    book.name("fix_base", sh, f"B{r}")
    r += 1
    put("fix_step_cost", "Доп. накладные на ступень выручки", A.FIX_STEP["step_cost"][0], "₽/мес", A.FIX_STEP["step_cost"][1], RUB)
    put("fix_rev_step", "Ступень выручки", A.FIX_STEP["rev_step"][0], "₽/мес", A.FIX_STEP["rev_step"][1], RUB)

    def capex_table(title, items, total_name):
        nonlocal r
        section(ws, r, title); r += 1
        header_row(ws, r, ["Позиция", "Цена за ед., ₽", "Кол-во", "Сумма, ₽"]); r += 1
        c0 = r
        for label, qty, price in items:
            ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
            style_cell(ws.cell(row=r, column=2, value=price), F_IN, RUB)
            style_cell(ws.cell(row=r, column=3, value=qty), F_IN, "0")
            style_cell(ws.cell(row=r, column=4, value=f"=B{r}*C{r}"), F_CALC, RUB)
            r += 1
        ws.cell(row=r, column=1, value="Итого").font = F_BOLD
        style_cell(ws.cell(row=r, column=4, value=f"=SUM(D{c0}:D{r - 1})"), F_CALC, RUB, FILL_TOTAL, bold=True)
        book.name(total_name, sh, f"D{r}")
        r += 1

    capex_table("CAPEX — стартовое оборудование и запуск (M0). Цены — ориентиры 2026, проверить у поставщиков", A.CAPEX_ITEMS, "capex_base")
    capex_table("CAPEX 2-го этапа (месяц покупки — на листе «Сценарии»)", A.CAPEX2_ITEMS, "capex2_total")

    section(ws, r, "Предзапусковые расходы (M0)"); r += 1
    p0 = r
    for label, val in A.PRELAUNCH_ITEMS:
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        style_cell(ws.cell(row=r, column=2, value=val), F_IN, RUB)
        ws.cell(row=r, column=3, value="₽").font = Font(name=FONT)
        r += 1
    ws.cell(row=r, column=1, value="Предзапуск, итого").font = F_BOLD
    style_cell(ws.cell(row=r, column=2, value=f"=SUM(B{p0}:B{r - 1})"), F_CALC, RUB, FILL_TOTAL, bold=True)
    book.name("prelaunch_total", sh, f"B{r}")
    r += 1
    put("reserve_safety", "Запас к макс. кассовому разрыву (пессимист.)", A.RESERVE_SAFETY[0], "x", A.RESERVE_SAFETY[1], NUM2)

    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 110
    ws.freeze_panes = "A4"


# ---------------------------------------------------------------- Сценарии

def sheet_scenarios(book):
    ws = book.wb.create_sheet("Сценарии")
    sh = ws.title
    ws["A1"] = "Сценарии: объёмы, отток, CAC"
    ws["A1"].font = F_TITLE
    header_row(ws, 3, ["Параметр", *A.SCENARIO_NAMES])
    r = 4
    key = {"a_m6", "s_m6", "churn", "cac_a", "cac_b"}
    for k, (label, *vals) in A.SCENARIOS.items():
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        for j, val in enumerate(vals):
            fmt = PCT if isinstance(val, float) and val < 1 else ("0" if val < 100 else RUB)
            c = ws.cell(row=r, column=2 + j, value=val)
            style_cell(c, F_IN, fmt, FILL_KEY if k in key else None)
            book.name(f"sc_{k}_{A.SCENARIO_CODES[j]}", sh, f"{get_column_letter(2 + j)}{r}")
        r += 1
    ws.column_dimensions["A"].width = 58
    for col in "BCD":
        ws.column_dimensions[col].width = 18


# ---------------------------------------------------------------- Юнит-экономика

def sheet_units(book):
    ws = book.wb.create_sheet("Юнит-экономика")
    sh = ws.title
    ws["A1"] = "Юнит-экономика по типам заказов"
    ws["A1"].font = F_TITLE
    r = 3

    def block(title, rows):
        nonlocal r
        header_row(ws, r, [title, "₽ / значение", "% от чека", "Комментарий"]); r += 1
        for label, formula, name, fmt, pct_of, note, total in rows:
            ws.cell(row=r, column=1, value=label).font = F_BOLD if total else Font(name=FONT)
            c = ws.cell(row=r, column=2, value=formula)
            style_cell(c, F_CALC, fmt, FILL_TOTAL if total else None, bold=total)
            if pct_of:
                style_cell(ws.cell(row=r, column=3, value=f"=IF({pct_of}=0,0,B{r}/{pct_of})"), F_CALC, PCT)
            if note:
                ws.cell(row=r, column=4, value=note).font = F_NOTE
            if name:
                book.name(name, sh, f"B{r}")
            r += 1
        r += 1

    block("Тип A — генеральная / после ремонта", [
        ("Средневзвешенная цена, ₽/м²", "=UA_price_general_m2*(1-UA_share_repair)+UA_price_repair_m2*UA_share_repair", "price_m2_a", RUB, None, "", False),
        ("Средний чек (AOV)", "=UA_area*price_m2_a+UA_upsell", "aov_a", RUB, "aov_a", "Площадь × цена + допчек", True),
        ("Оплата клинеров", "=aov_a*UA_labor_share", "labor_a", RUB, "aov_a", "", False),
        ("Химия и расходники", "=UA_chem", None, RUB, "aov_a", "", False),
        ("Амортизация оборудования", "=UA_amort", None, RUB, "aov_a", "", False),
        ("Логистика", "=UA_logistics", None, RUB, "aov_a", "", False),
        ("Эквайринг / СБП", "=aov_a*acquiring", None, RUB, "aov_a", "", False),
        ("Резерв качества (переделки, компенсации)", "=aov_a*UA_quality_reserve", None, RUB, "aov_a", "", False),
        ("Переменные затраты (COGS)", "=SUM(B6:B11)", "var_a", RUB, "aov_a", "", True),
        ("Валовая прибыль", "=aov_a-var_a", "gm_a", RUB, "aov_a", "", True),
        ("УСН", "=aov_a*usn_rate", None, RUB, "aov_a", "", False),
        ("Маржинальный доход до CAC", "=gm_a-B14", "cm_a", RUB, "aov_a", "Сколько заказ приносит на покрытие FIX и маркетинга", True),
        ("Оплата клинера за чел-час", "=labor_a/UA_man_hours", None, RUB, None, "Ориентир рынка Тюмени: 300–450 ₽/ч", False),
        ("Оплата клинеров за м²", "=labor_a/UA_area", None, RUB, None, "", False),
        ("Допустимый CAC при целевой марже", "=cm_a-target_margin_a*aov_a", "cac_max_a", RUB, "aov_a", "Маржа после CAC не ниже целевой", True),
        ("CAC безубыточности заказа", "=cm_a", None, RUB, "aov_a", "Выше — каждый заказ в минус", False),
        ("Допустимая цена лида (CPL)", "=cac_max_a*lead_to_order_a", "cpl_max_a", RUB, None, "При конверсии лид → заказ из «Допущений»", True),
    ])

    b0 = r
    block("Тип B — поддерживающая (подписка), на 1 визит", [
        ("Цена визита по подписке", "=UB_price_single*(1-UB_sub_discount)", "price_b", RUB, "price_b", "Разовая цена − средняя скидка подписки", True),
        ("Оплата клинера", "=price_b*UB_labor_share", "labor_b", RUB, "price_b", "", False),
        ("Химия и расходники", "=UB_chem", None, RUB, "price_b", "", False),
        ("Амортизация инвентаря", "=UB_amort", None, RUB, "price_b", "", False),
        ("Проезд клинера", "=UB_logistics", None, RUB, "price_b", "", False),
        ("Эквайринг / СБП", "=price_b*acquiring", None, RUB, "price_b", "", False),
        ("Резерв качества", "=price_b*UB_quality_reserve", None, RUB, "price_b", "", False),
        ("Переменные затраты на визит", f"=SUM(B{b0 + 2}:B{b0 + 7})", "var_b", RUB, "price_b", "", True),
        ("Валовая прибыль на визит", "=price_b-var_b", "gm_b", RUB, "price_b", "", True),
        ("УСН", "=price_b*usn_rate", None, RUB, "price_b", "", False),
        ("Маржинальный доход на визит", f"=gm_b-B{b0 + 10}", "cm_b", RUB, "price_b", "", True),
        ("Оплата клинера за час", "=labor_b/UB_hours", None, RUB, None, "", False),
        ("Выручка с подписчика в месяц", "=price_b*UB_visits_per_month", "rev_month_b", RUB, None, "", True),
        ("Маржинальный доход с подписчика в месяц", "=cm_b*UB_visits_per_month", "cm_month_b", RUB, None, "", True),
    ])

    header_row(ws, r, ["LTV подписчика по сценариям", *A.SCENARIO_NAMES]); r += 1
    ltv_rows = [
        ("Отток в месяц", lambda c: f"=sc_churn_{c}", PCT),
        ("Средний срок жизни, мес (1 / отток)", lambda c: f"=1/sc_churn_{c}", NUM1),
        ("LTV по выручке", lambda c: f"=rev_month_b/sc_churn_{c}", RUB),
        ("LTV по маржинальному доходу", lambda c: f"=cm_month_b/sc_churn_{c}", RUB),
        ("Макс. CAC при LTV/CAC ≥ цели", lambda c: f"=cm_month_b/sc_churn_{c}/ltv_cac_min", RUB),
        ("Макс. CAC при окупаемости ≤ N мес", lambda c: "=cm_month_b*payback_months_b", RUB),
        ("CAC в сценарии", lambda c: f"=sc_cac_b_{c}", RUB),
        ("LTV / CAC в сценарии", lambda c: f"=cm_month_b/sc_churn_{c}/sc_cac_b_{c}", NUM1),
        ("Окупаемость CAC, мес", lambda c: f"=sc_cac_b_{c}/cm_month_b", NUM1),
    ]
    for label, fn, fmt in ltv_rows:
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        for j, code in enumerate(A.SCENARIO_CODES):
            style_cell(ws.cell(row=r, column=2 + j, value=fn(code)), F_CALC, fmt)
        r += 1
    r += 1

    header_row(ws, r, ["Прежний прайс сайта vs рекомендуемый (2-комн., 1 санузел)", "Прежний: доля ФОТ как в модели", "Прежний: рыночная ставка клинера", "Рекомендуемый прайс"]); r += 1
    cur_gen = "(cur_gen_base+cur_rooms*cur_gen_room+cur_baths*cur_gen_bath)"
    cur_post = "(cur_post_base+cur_rooms*cur_post_room+cur_baths*cur_post_bath)"
    cur_maint = "(cur_maint_base+cur_rooms*cur_maint_room+cur_baths*cur_maint_bath)"
    cur_aov_a = f"({cur_gen}*(1-UA_share_repair)+{cur_post}*UA_share_repair+UA_upsell)"
    cur_price_b = f"({cur_maint}*(1-UB_sub_discount))"
    var_rate_a = "(acquiring+UA_quality_reserve+usn_rate)"
    var_rate_b = "(acquiring+UB_quality_reserve+usn_rate)"
    fixed_a = "(UA_chem+UA_amort+UA_logistics)"
    fixed_b = "(UB_chem+UB_amort+UB_logistics)"
    cmp_rows = [
        ("Генеральная, ₽", f"={cur_gen}", f"={cur_gen}", "=UA_area*UA_price_general_m2", RUB),
        ("После ремонта, ₽", f"={cur_post}", f"={cur_post}", "=UA_area*UA_price_repair_m2", RUB),
        ("Норма времени: генеральная / после ремонта (движок), ч", "=(cur_gen_min+cur_post_min)/2/60", "=(cur_gen_min+cur_post_min)/2/60", "=UA_man_hours", NUM1),
        ("Средний чек A (с допчеком)", f"={cur_aov_a}", f"={cur_aov_a}", "=aov_a", RUB),
        ("Оплата клинеров A, ₽", f"={cur_aov_a}*UA_labor_share", "=labor_a", "=labor_a", RUB),
        ("… доля от чека", "=UA_labor_share", f"=labor_a/{cur_aov_a}", "=UA_labor_share", PCT),
        ("… ставка клинера при трудоёмкости модели, ₽/чел-ч", f"={cur_aov_a}*UA_labor_share/UA_man_hours", "=labor_a/UA_man_hours", "=labor_a/UA_man_hours", RUB),
        ("Маржинальный доход A до CAC", f"={cur_aov_a}*(1-UA_labor_share-{var_rate_a})-{fixed_a}", f"={cur_aov_a}*(1-{var_rate_a})-labor_a-{fixed_a}", "=cm_a", RUB),
        ("… маржинальность A", f"=({cur_aov_a}*(1-UA_labor_share-{var_rate_a})-{fixed_a})/{cur_aov_a}", f"=({cur_aov_a}*(1-{var_rate_a})-labor_a-{fixed_a})/{cur_aov_a}", "=cm_a/aov_a", PCT),
        ("Поддерживающая разово, ₽", f"={cur_maint}", f"={cur_maint}", "=UB_price_single", RUB),
        ("Визит по подписке, ₽", f"={cur_price_b}", f"={cur_price_b}", "=price_b", RUB),
        ("Ставка клинера на визите, ₽/ч", f"={cur_price_b}*UB_labor_share/UB_hours", "=labor_b/UB_hours", "=labor_b/UB_hours", RUB),
        ("Маржинальный доход на визит", f"={cur_price_b}*(1-UB_labor_share-{var_rate_b})-{fixed_b}", f"={cur_price_b}*(1-{var_rate_b})-labor_b-{fixed_b}", "=cm_b", RUB),
        ("Маржинальный доход с подписчика в месяц", f"=({cur_price_b}*(1-UB_labor_share-{var_rate_b})-{fixed_b})*UB_visits_per_month", f"=({cur_price_b}*(1-{var_rate_b})-labor_b-{fixed_b})*UB_visits_per_month", "=cm_month_b", RUB),
    ]
    CMP_ROWS.clear()
    for label, f1, f2, f3, fmt in cmp_rows:
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        for j, f in enumerate((f1, f2, f3)):
            style_cell(ws.cell(row=r, column=2 + j, value=f), F_CALC, fmt)
        CMP_ROWS[label] = r
        r += 1
    ws.cell(row=r, column=1, value="Трудоёмкость модели: генеральная ~12, после ремонта ~16 чел-ч; FAQ сайта: «2 специалиста на 4–6 часов» для генеральной 2-комн.").font = F_NOTE
    r += 2

    s0 = r
    block("Тип S — спецуслуги (химчистка мебели, окна)", [
        ("Средний чек", "=US_aov", "aov_s", RUB, "aov_s", "", True),
        ("Оплата мастера", "=aov_s*US_labor_share", None, RUB, "aov_s", "", False),
        ("Химия", "=US_chem", None, RUB, "aov_s", "", False),
        ("Амортизация", "=US_amort", None, RUB, "aov_s", "", False),
        ("Логистика", "=US_logistics", None, RUB, "aov_s", "", False),
        ("Эквайринг / СБП", "=aov_s*acquiring", None, RUB, "aov_s", "", False),
        ("Резерв качества", "=aov_s*US_quality_reserve", None, RUB, "aov_s", "", False),
        ("Переменные затраты", f"=SUM(B{s0 + 2}:B{s0 + 7})", "var_s", RUB, "aov_s", "", True),
        ("Валовая прибыль", "=aov_s-var_s", None, RUB, "aov_s", "", True),
        ("УСН", "=aov_s*usn_rate", None, RUB, "aov_s", "", False),
        ("Маржинальный доход", f"=B{s0 + 9}-B{s0 + 10}", "cm_s", RUB, "aov_s", "", True),
    ])

    block("B2B — договор на обслуживание офиса, в месяц", [
        ("Сумма договора", "=b2b_value", None, RUB, "b2b_value", "", True),
        ("Прямые затраты", "=b2b_value*b2b_direct_share", "b2b_direct", RUB, "b2b_value", "", False),
        ("УСН", "=b2b_value*usn_rate", None, RUB, "b2b_value", "", False),
        ("Маржинальный доход", f"=b2b_value-b2b_direct-B{r + 3}", "cm_b2b", RUB, "b2b_value", "", True),
    ])

    ws.column_dimensions["A"].width = 48
    for col in "BCD":
        ws.column_dimensions[col].width = 18
    ws.column_dimensions["D"].width = 60


# ---------------------------------------------------------------- ОПиУ

ROWS = {}
CMP_ROWS = {}


def sheet_pnl(book, code):
    ws = book.wb.create_sheet(SCN_SHEETS[code])
    name = A.SCENARIO_NAMES[A.SCENARIO_CODES.index(code)]
    ws["A1"] = f"ОПиУ и денежный поток — сценарий «{name}», ₽"
    ws["A1"].font = F_TITLE
    first, last = 3, 3 + A.HORIZON - 1
    FC, LC = get_column_letter(first), get_column_letter(last)

    def sc(k):
        return f"sc_{k}_{code}"

    lines = [
        # key, label, formula(col, L, prev), fmt, total_kind, bold
        ("m", "Месяц №", None, "0", None, True),
        ("year", "Год", lambda c, L, p: f"=start_year+INT((start_month-1+{c}{L['m']}-1)/12)", "0", None, False),
        ("cal", "Календарный месяц", lambda c, L, p: f"=MOD(start_month-1+{c}{L['m']}-1,12)+1", "0", None, False),
        ("season", "Индекс сезонности", lambda c, L, p: f"=INDEX(season_tbl,{c}{L['cal']})", NUM2, None, False),
        None,
        ("hdr_vol", "ОБЪЁМЫ", None, None, None, True),
        ("a_base", "Заказы A до сезонности", lambda c, L, p: f"=IF({c}{L['m']}<=6,{sc('a_start')}+({sc('a_m6')}-{sc('a_start')})*({c}{L['m']}-1)/5,{sc('a_m6')}*(1+{sc('a_growth')})^({c}{L['m']}-6))", NUM1, None, False),
        ("a", "Заказы A (генеральная / после ремонта)", lambda c, L, p: f"=MIN({sc('a_cap')},{c}{L['a_base']}*{c}{L['season']})", NUM1, "sum", False),
        ("new_subs", "Новые подписчики B", lambda c, L, p: f"=IF({c}{L['m']}<=6,{sc('s_start')}+({sc('s_m6')}-{sc('s_start')})*({c}{L['m']}-1)/5,{sc('s_m6')}*(1+{sc('s_growth')})^({c}{L['m']}-6))", NUM1, "sum", False),
        ("active", "Активные подписчики B", lambda c, L, p: (f"={c}{L['new_subs']}" if p is None else f"={p}{L['active']}*(1-{sc('churn')})+{c}{L['new_subs']}"), NUM1, None, False),
        ("visits", "Визиты B", lambda c, L, p: f"={c}{L['active']}*UB_visits_per_month", NUM1, "sum", False),
        ("spec", "Заказы спецуслуг S", lambda c, L, p: f"={c}{L['a']}*{sc('spec_ratio')}", NUM1, "sum", False),
        ("b2b", "Действующие B2B-договоры", lambda c, L, p: f"=IF({c}{L['m']}>={sc('b2b_start')},MIN({sc('b2b_max')},INT(({c}{L['m']}-{sc('b2b_start')})/{sc('b2b_step')})+1),0)", "0", None, False),
        ("fte", "Потребность в клинерах, FTE", lambda c, L, p: f"=({c}{L['a']}*UA_man_hours+{c}{L['visits']}*UB_hours+{c}{L['spec']}*US_man_hours)/hours_per_fte+{c}{L['b2b']}*b2b_fte", NUM1, None, False),
        None,
        ("hdr_pl", "ОПиУ", None, None, None, True),
        ("rev_a", "Выручка A", lambda c, L, p: f"={c}{L['a']}*aov_a", RUB, "sum", False),
        ("rev_b", "Выручка B (подписка)", lambda c, L, p: f"={c}{L['visits']}*price_b", RUB, "sum", False),
        ("rev_s", "Выручка S (спецуслуги)", lambda c, L, p: f"={c}{L['spec']}*aov_s", RUB, "sum", False),
        ("rev_b2b", "Выручка B2B", lambda c, L, p: f"={c}{L['b2b']}*b2b_value", RUB, "sum", False),
        ("rev", "ВЫРУЧКА", lambda c, L, p: f"=SUM({c}{L['rev_a']}:{c}{L['rev_b2b']})", RUB, "sum", True),
        ("var", "Переменные затраты (ФОТ клинеров, химия, логистика, эквайринг, резерв)", lambda c, L, p: f"={c}{L['a']}*var_a+{c}{L['visits']}*var_b+{c}{L['spec']}*var_s+{c}{L['b2b']}*b2b_direct", RUB, "sum", False),
        ("gm", "Валовая прибыль", lambda c, L, p: f"={c}{L['rev']}-{c}{L['var']}", RUB, "sum", True),
        ("mkt", "Маркетинг (CAC: партнёрам, продвижение, скидка 1-го визита)", lambda c, L, p: f"={c}{L['a']}*{sc('cac_a')}+{c}{L['new_subs']}*{sc('cac_b')}+{c}{L['spec']}*{sc('cac_s')}", RUB, "sum", False),
        ("fix", "Постоянные расходы (FIX)", lambda c, L, p: f"=fix_base+fix_step_cost*INT({c}{L['rev']}/fix_rev_step)", RUB, "sum", False),
        ("vat_on", "НДС применяется (1 = да)", lambda c, L, p: f"=IF(OR(SUMIFS(${FC}${L['rev']}:${LC}${L['rev']},${FC}${L['year']}:${LC}${L['year']},{c}{L['year']}-1)>vat_threshold,SUMIFS(${FC}${L['rev']}:${LC}${L['rev']},${FC}${L['year']}:${LC}${L['year']},{c}{L['year']},${FC}${L['m']}:${LC}${L['m']},\"<\"&{c}{L['m']})>vat_threshold),1,0)", "0", None, False),
        ("vat", "НДС (выделяется из цены)", lambda c, L, p: f"={c}{L['rev']}*vat_rate/(1+vat_rate)*{c}{L['vat_on']}", RUB, "sum", False),
        ("usn", "УСН", lambda c, L, p: f"=({c}{L['rev']}-{c}{L['vat']})*usn_rate", RUB, "sum", False),
        ("profit", "ОПЕРАЦИОННАЯ ПРИБЫЛЬ", lambda c, L, p: f"={c}{L['rev']}-{c}{L['vat']}-{c}{L['var']}-{c}{L['mkt']}-{c}{L['fix']}-{c}{L['usn']}", RUB, "sum", True),
        ("margin", "Рентабельность по операционной прибыли", lambda c, L, p: f"=IF({c}{L['rev']}=0,0,{c}{L['profit']}/{c}{L['rev']})", PCT, "margin", False),
        None,
        ("hdr_cf", "ДЕНЕЖНЫЙ ПОТОК", None, None, None, True),
        ("capex", "CAPEX 2-го этапа", lambda c, L, p: f"=IF({c}{L['m']}={sc('capex2_month')},capex2_total,0)", RUB, "sum", False),
        ("cf", "Денежный поток месяца", lambda c, L, p: f"={c}{L['profit']}-{c}{L['capex']}", RUB, "sum", True),
        ("cum_op", "Накопленный ДП без стартовых вложений", lambda c, L, p: (f"={c}{L['cf']}" if p is None else f"={p}{L['cum_op']}+{c}{L['cf']}"), RUB, None, False),
        ("cum", "Накопленный ДП с учётом CAPEX и предзапуска (M0)", lambda c, L, p: (f"=-(capex_base+prelaunch_total)+{c}{L['cf']}" if p is None else f"={p}{L['cum']}+{c}{L['cf']}"), RUB, None, True),
        ("sustained", "Служебная: месяц, после которого нет убыточных месяцев", lambda c, L, p: f"=IF(COUNTIF({c}{L['profit']}:${LC}${L['profit']},\"<0\")=0,{c}{L['m']},\"\")", "0", None, False),
    ]

    L = {}
    row = 3
    for item in lines:
        if item is None:
            row += 1
            continue
        L[item[0]] = row
        row += 1

    header_row(ws, 2, ["Показатель", "Итого 24 мес"] + [
        f"M{m}\n{MONTH_NAMES[M.calendar(m)[1] - 1]} {str(M.calendar(m)[0])[2:]}" for m in range(1, A.HORIZON + 1)])
    ws.row_dimensions[2].height = 30

    for item in lines:
        if item is None:
            continue
        key, label, fn, fmt, total, bold = item
        rr = L[key]
        lc = ws.cell(row=rr, column=1, value=label)
        lc.font = F_BOLD if bold else Font(name=FONT)
        if key.startswith("hdr"):
            for col in range(1, last + 1):
                ws.cell(row=rr, column=col).fill = FILL_SEC
            continue
        for k in range(A.HORIZON):
            col = first + k
            c = get_column_letter(col)
            p = get_column_letter(col - 1) if k > 0 else None
            cell = ws.cell(row=rr, column=col)
            if key == "m":
                cell.value = k + 1
                style_cell(cell, F_IN, fmt, bold=True)
            else:
                cell.value = fn(c, L, p)
                style_cell(cell, F_CALC, fmt, FILL_TOTAL if bold else None, bold=bold)
        if total == "sum":
            style_cell(ws.cell(row=rr, column=2, value=f"=SUM({FC}{rr}:{LC}{rr})"), F_CALC, fmt, FILL_TOTAL, bold=True)
        elif total == "margin":
            style_cell(ws.cell(row=rr, column=2, value=f"=IF(B{L['rev']}=0,0,B{L['profit']}/B{L['rev']})"), F_CALC, PCT, FILL_TOTAL, bold=True)

    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 15
    for k in range(A.HORIZON):
        ws.column_dimensions[get_column_letter(first + k)].width = 12
    ws.freeze_panes = "C3"
    ROWS.update(L)
    return L, FC, LC


# ---------------------------------------------------------------- Сводка

def sheet_summary(book, L, FC, LC):
    ws = book.wb.create_sheet("Сводка", 1)
    ws["A1"] = "Сводка по сценариям"
    ws["A1"].font = F_TITLE
    header_row(ws, 3, ["Показатель", *A.SCENARIO_NAMES, "Комментарий"])
    M12 = get_column_letter(3 + 11)
    M24 = LC

    def ref(code, rng):
        return f"{q(SCN_SHEETS[code])}!{rng}"

    metrics = [
        ("Выручка за первые 12 мес", lambda c: f"=SUM({ref(c, f'{FC}{L['rev']}:{M12}{L['rev']}')})", RUB, ""),
        ("Выручка за 24 мес", lambda c: f"={ref(c, f'B{L['rev']}')}", RUB, ""),
        ("Выручка в M12 (окт 2027)", lambda c: f"={ref(c, f'{M12}{L['rev']}')}", RUB, ""),
        ("Выручка в M24 (окт 2028)", lambda c: f"={ref(c, f'{M24}{L['rev']}')}", RUB, ""),
        ("Операционная прибыль за 12 мес", lambda c: f"=SUM({ref(c, f'{FC}{L['profit']}:{M12}{L['profit']}')})", RUB, ""),
        ("Операционная прибыль за 24 мес", lambda c: f"={ref(c, f'B{L['profit']}')}", RUB, ""),
        ("Операционная прибыль в M12", lambda c: f"={ref(c, f'{M12}{L['profit']}')}", RUB, ""),
        ("Операционная прибыль в M24", lambda c: f"={ref(c, f'{M24}{L['profit']}')}", RUB, ""),
        ("Рентабельность за 24 мес", lambda c: f"={ref(c, f'B{L['margin']}')}", PCT, ""),
        ("Месяц устойчивой безубыточности", lambda c: f"=IF(MIN({ref(c, f'{FC}{L['sustained']}:{LC}{L['sustained']}')})=0,\"> 24\",MIN({ref(c, f'{FC}{L['sustained']}:{LC}{L['sustained']}')}))", "0", "Первый месяц, начиная с которого нет убыточных месяцев"),
        ("Срок окупаемости вложений, мес", lambda c: f"=IF(_xlfn.MINIFS({ref(c, f'{FC}{L['m']}:{LC}{L['m']}')},{ref(c, f'{FC}{L['cum']}:{LC}{L['cum']}')},\">=0\")=0,\"> 24\",_xlfn.MINIFS({ref(c, f'{FC}{L['m']}:{LC}{L['m']}')},{ref(c, f'{FC}{L['cum']}:{LC}{L['cum']}')},\">=0\"))", "0", "Накопленный ДП с учётом CAPEX и предзапуска ≥ 0"),
        ("Максимальный кассовый разрыв (операционный)", lambda c: f"=-MIN(0,MIN({ref(c, f'{FC}{L['cum_op']}:{LC}{L['cum_op']}')}))", RUB, "Без стартовых вложений; включает CAPEX 2-го этапа"),
        ("Минимум накопленного ДП (с вложениями)", lambda c: f"=MIN({ref(c, f'{FC}{L['cum']}:{LC}{L['cum']}')})", RUB, "Пиковая потребность в деньгах"),
        ("Первый месяц с НДС 5%", lambda c: f"=IF(_xlfn.MINIFS({ref(c, f'{FC}{L['m']}:{LC}{L['m']}')},{ref(c, f'{FC}{L['vat_on']}:{LC}{L['vat_on']}')},1)=0,\"нет\",_xlfn.MINIFS({ref(c, f'{FC}{L['m']}:{LC}{L['m']}')},{ref(c, f'{FC}{L['vat_on']}:{LC}{L['vat_on']}')},1))", "0", "Порог 20 млн ₽ выручки в календарный год"),
        ("Активные подписчики в M24", lambda c: f"={ref(c, f'{M24}{L['active']}')}", RUB, ""),
        ("Клинеров (FTE) в M12", lambda c: f"={ref(c, f'{M12}{L['fte']}')}", NUM1, ""),
        ("Клинеров (FTE) в M24", lambda c: f"={ref(c, f'{M24}{L['fte']}')}", NUM1, ""),
    ]
    r = 4
    for label, fn, fmt, note in metrics:
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        for j, code in enumerate(A.SCENARIO_CODES):
            style_cell(ws.cell(row=r, column=2 + j, value=fn(code)), F_LINK, fmt)
        ws.cell(row=r, column=5, value=note).font = F_NOTE
        if label.startswith("Максимальный кассовый"):
            book.name("max_gap_P", ws.title, f"B{r}")
            book.name("max_gap_R", ws.title, f"C{r}")
        r += 1

    r += 1
    header_row(ws, r, ["Стартовый капитал", "Минимальный", "Рекомендуемый", "", "Комментарий"]); r += 1
    cap_rows = [
        ("CAPEX: оборудование, брендинг, сайт", "=capex_base", "=capex_base", "Лист «Допущения»"),
        ("Предзапуск: рекрутинг, стажировка, юрист, стартовое продвижение", "=prelaunch_total", "=prelaunch_total", ""),
        ("Резерв на кассовый разрыв", "=max_gap_R*reserve_safety", "=max_gap_P*reserve_safety", "Мин. — по реалистичному, рекоменд. — по пессимистичному сценарию × запас"),
    ]
    c0 = r
    for label, f1, f2, note in cap_rows:
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        style_cell(ws.cell(row=r, column=2, value=f1), F_CALC, RUB)
        style_cell(ws.cell(row=r, column=3, value=f2), F_CALC, RUB)
        ws.cell(row=r, column=5, value=note).font = F_NOTE
        r += 1
    ws.cell(row=r, column=1, value="ИТОГО порог входа").font = F_BOLD
    style_cell(ws.cell(row=r, column=2, value=f"=SUM(B{c0}:B{r - 1})"), F_CALC, RUB, FILL_TOTAL, bold=True)
    style_cell(ws.cell(row=r, column=3, value=f"=SUM(C{c0}:C{r - 1})"), F_CALC, RUB, FILL_TOTAL, bold=True)
    book.name("start_capital_min", ws.title, f"B{r}")
    book.name("start_capital_rec", ws.title, f"C{r}")
    r += 2

    header_row(ws, r, ["Точка безубыточности (FIX базовый)", *A.SCENARIO_NAMES, "Комментарий"]); r += 1
    be_rows = [
        ("FIX базовый, ₽/мес", lambda c: "=fix_base", RUB, ""),
        ("Маржинальный доход заказа A после CAC", lambda c: f"=cm_a-sc_cac_a_{c}", RUB, ""),
        ("Только заказы A, шт/мес", lambda c: f"=fix_base/(cm_a-sc_cac_a_{c})", NUM1, "Если весь доход — от генеральных/после ремонта"),
        ("… в день", lambda c: f"=fix_base/(cm_a-sc_cac_a_{c})/30", NUM1, ""),
        ("Только подписка: визитов в месяц", lambda c: "=fix_base/cm_b", NUM1, "CAC подписчика окупается за 1–2 мес, здесь не учтён"),
        ("… это активных подписчиков", lambda c: "=fix_base/cm_b/UB_visits_per_month", NUM1, ""),
        ("Микс: при 30 активных подписчиках нужно заказов A", lambda c: f"=MAX(0,(fix_base-30*cm_month_b)/(cm_a-sc_cac_a_{c}))", NUM1, "Подписка закрывает половину FIX, остальное — заказы A"),
    ]
    for label, fn, fmt, note in be_rows:
        ws.cell(row=r, column=1, value=label).font = Font(name=FONT)
        for j, code in enumerate(A.SCENARIO_CODES):
            style_cell(ws.cell(row=r, column=2 + j, value=fn(code)), F_CALC, fmt)
        ws.cell(row=r, column=5, value=note).font = F_NOTE
        r += 1

    ws.column_dimensions["A"].width = 58
    for col in "BCD":
        ws.column_dimensions[col].width = 18
    ws.column_dimensions["E"].width = 70


def build():
    book = Book()
    sheet_readme(book)
    sheet_assumptions(book)
    sheet_scenarios(book)
    sheet_units(book)
    L = FC = LC = None
    for code in A.SCENARIO_CODES:
        L, FC, LC = sheet_pnl(book, code)
    sheet_summary(book, L, FC, LC)
    book.wb.save(XLSX)
    return L


# ---------------------------------------------------------------- Markdown-выгрузка

def fmt_rub(x):
    return f"{x:,.0f}".replace(",", " ")


def write_markdown():
    ua, ub, us, b2b = M.unit_a(), M.unit_b(), M.unit_s(), M.unit_b2b()
    out = ["# Выгрузка финмодели (сгенерировано build_finmodel.py)", "",
           "Не редактируйте вручную: файл пересобирается из `model/assumptions.py`.", ""]
    out += ["## Сводка по сценариям", "",
            "| Показатель | " + " | ".join(A.SCENARIO_NAMES) + " |", "|---|---:|---:|---:|"]
    sms = {c: M.summary(c) for c in A.SCENARIO_CODES}
    def row(label, key, f=fmt_rub):
        vals = []
        for c in A.SCENARIO_CODES:
            val = sms[c][key]
            vals.append("> 24" if val is None and key in ("breakeven_month", "payback_month") else
                        ("нет" if val is None else (f(val) if not isinstance(val, int) or key not in ("breakeven_month", "payback_month", "vat_from") else str(val))))
        out.append(f"| {label} | " + " | ".join(vals) + " |")
    row("Выручка за 12 мес, ₽", "rev_12")
    row("Выручка за 24 мес, ₽", "rev_24")
    row("Выручка в M12, ₽/мес", "rev_m12")
    row("Выручка в M24, ₽/мес", "rev_m24")
    row("Операц. прибыль за 12 мес, ₽", "profit_12")
    row("Операц. прибыль за 24 мес, ₽", "profit_24")
    row("Операц. прибыль в M12, ₽/мес", "profit_m12")
    row("Операц. прибыль в M24, ₽/мес", "profit_m24")
    row("Месяц устойчивой безубыточности", "breakeven_month")
    row("Окупаемость вложений, мес", "payback_month")
    row("Макс. операционный кассовый разрыв, ₽", "max_gap")
    row("Минимум накопленного ДП, ₽", "min_cum")
    row("Первый месяц с НДС 5%", "vat_from")
    sc = M.start_capital()
    out += ["", "## Стартовый капитал", "",
            f"- CAPEX: {fmt_rub(sc['capex'])} ₽",
            f"- Предзапуск: {fmt_rub(sc['prelaunch'])} ₽",
            f"- Резерв (пессимистичный разрыв × {A.RESERVE_SAFETY[0]}): {fmt_rub(sc['reserve'])} ₽",
            f"- **Итого рекомендуемый порог входа: {fmt_rub(sc['total'])} ₽**", ""]
    cu = M.current_units()
    out += ["## Прежний прайс сайта (сиды до обновления) — реалистичный сценарий", "",
            "| Вариант | Окупаемость, мес | Прибыль за 12 мес, ₽ | Прибыль за 24 мес, ₽ | Макс. разрыв, ₽ |",
            "|---|---:|---:|---:|---:|"]
    base = sms["R"]
    out.append(f"| Рекомендуемый прайс (база модели) | {base['payback_month']} | {fmt_rub(base['profit_12'])} | {fmt_rub(base['profit_24'])} | {fmt_rub(base['max_gap'])} |")
    for mode, label in (("share", "Прежний прайс, ФОТ той же долей чека"), ("market", "Прежний прайс, рыночная ставка клинера")):
        sm = M.current_price_scenario(mode)
        pb = sm["payback_month"] if sm["payback_month"] else "> 24"
        out.append(f"| {label} | {pb} | {fmt_rub(sm['profit_12'])} | {fmt_rub(sm['profit_24'])} | {fmt_rub(sm['max_gap'])} |")
    out.append("")
    for code in A.SCENARIO_CODES:
        name = A.SCENARIO_NAMES[A.SCENARIO_CODES.index(code)]
        out += [f"## Помесячно — {name}", "",
                "| M | Месяц | Заказы A | Подписчики | Визиты B | Спец S | B2B | Выручка | Перем. | Маркетинг | FIX | Налоги | Прибыль | Накопл. ДП | FTE |",
                "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for r in sms[code]["rows"]:
            out.append(f"| {r['m']} | {MONTH_NAMES[r['month'] - 1]} {r['year']} | {r['a']:.0f} | {r['active']:.0f} | {r['visits']:.0f} | {r['spec']:.0f} | {r['contracts']} | "
                       f"{fmt_rub(r['rev'])} | {fmt_rub(r['var'])} | {fmt_rub(r['mkt'])} | {fmt_rub(r['fix'])} | {fmt_rub(r['vat'] + r['usn'])} | "
                       f"{fmt_rub(r['profit'])} | {fmt_rub(r['cum'])} | {r['fte']:.1f} |")
        out.append("")
    with open(MD, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


# ---------------------------------------------------------------- Проверка

def verify(L):
    recalc = os.environ.get("XLSX_RECALC")
    if not recalc:
        print("XLSX_RECALC не задан — пропускаю пересчёт", file=sys.stderr)
        return False
    res = subprocess.run([sys.executable, recalc, XLSX, "120"], capture_output=True, text=True)
    info = json.loads(res.stdout)
    print(json.dumps({k: info.get(k) for k in ("status", "total_formulas", "total_errors", "error_summary", "error")}, ensure_ascii=False))
    if info.get("status") != "success":
        return False
    wb = load_workbook(XLSX, data_only=True)
    ok = True
    for code in A.SCENARIO_CODES:
        ws = wb[SCN_SHEETS[code]]
        rows = M.run(code)
        for k, r in enumerate(rows):
            col = 3 + k
            for key in ("a", "active", "rev", "var", "mkt", "fix", "vat", "usn", "profit", "cum", "fte"):
                xl = ws.cell(row=L[key], column=col).value
                py = r[key]
                if xl is None or abs(xl - py) > max(0.5, abs(py) * 1e-9):
                    ok = False
                    print(f"MISMATCH {code} M{k + 1} {key}: excel={xl} python={py}")
    u = wb["Юнит-экономика"]
    cu = M.current_units()
    checks = {
        "Средний чек A (с допчеком)": (cu["aov_a"], cu["aov_a"]),
        "Маржинальный доход A до CAC": (cu["share"]["cm_a"], cu["market"]["cm_a"]),
        "Маржинальный доход на визит": (cu["share"]["cm_b"], cu["market"]["cm_b"]),
    }
    for label, (py1, py2) in checks.items():
        row = CMP_ROWS[label]
        for col, py in ((2, py1), (3, py2)):
            xl = u.cell(row=row, column=col).value
            if xl is None or abs(xl - py) > 0.5:
                ok = False
                print(f"MISMATCH current-price {label} col{col}: excel={xl} python={py}")
    s = wb["Сводка"]
    sc = M.start_capital()
    for row in s.iter_rows(min_row=1, max_row=s.max_row):
        if row[0].value == "ИТОГО порог входа":
            if abs(row[2].value - sc["total"]) > 1:
                ok = False
                print("MISMATCH start capital", row[2].value, sc["total"])
            print("Порог входа (Excel): минимальный", round(row[1].value), "рекомендуемый", round(row[2].value))
        if row[0].value in ("Месяц устойчивой безубыточности", "Срок окупаемости вложений, мес", "Первый месяц с НДС 5%"):
            print(row[0].value, [c.value for c in row[1:4]])
    print("VERIFY", "OK" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    L = build()
    write_markdown()
    print("Собрано:", XLSX)
    if "--verify" in sys.argv:
        sys.exit(0 if verify(L) else 1)
