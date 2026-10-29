"""Визитки под печать: 90×50 мм, вылеты 2 мм (файл 94×54 мм), текст в кривых, двусторонний PDF в CMYK.

    python3 marketing/tools/build_cards.py      → marketing/print/business-cards/

Общая визитка компании печатается как есть. Именные собираются из списка PEOPLE ниже: впишите имя, должность
и телефон сотрудника и перезапустите скрипт. Дерзкие «перевёртыши» — список HOOKS, трендовые (коллекционная серия
50×90 мм, тактильная с маской выборочного лака, яркий маркер) — trend_cards(). Контакты Тюмени — из apps/web/lib/city.ts.
Для перевода в CMYK нужен Ghostscript (gs); без него остаётся RGB-PDF, и в CMYK переводит типография.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys

import segno
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

sys.path.insert(0, os.path.dirname(__file__))
import brandkit as B  # noqa: E402
import illustrations as I  # noqa: E402

TOOLS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(TOOLS, "..", "print", "business-cards"))

TRIM_W, TRIM_H, BLEED, SAFE = 90.0, 50.0, 2.0, 4.0
W, H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED
X0, Y0 = BLEED + SAFE, BLEED + SAFE                 # левый верхний угол безопасной зоны
X1, Y1 = BLEED + TRIM_W - SAFE, BLEED + TRIM_H - SAFE

PHONE = "+7 (912) 395-20-43"                         # apps/web/lib/city.ts, tyumen.phone
SITE = "tyumen.cleanliness.pro"
VK = "vk.ru/cleanliness_tmn"
QR_URL = "https://tyumen.cleanliness.pro/?utm_source=business_card&utm_medium=offline&utm_campaign=tyumen"
MUTED_DARK = "#B6C3D3"
PREVIEW_PX = 12                                     # превью: 12 px на мм (≈ 300 dpi)

# Именные визитки: (файл, имя, должность, телефон). Пример — шаблон; замените на реальных людей.
PEOPLE = [
    ("sample", "[Имя Фамилия]", "Менеджер по работе с клиентами", PHONE),
]

# Фирменные CMYK из marketing/brand/README.md: после перевода в CMYK плашки бренда заменяются точными значениями.
BRAND_CMYK = {
    "#0B2A4A": (1.00, 0.75, 0.35, 0.40),   # тёмно-синий, Pantone 2965 C
    "#0369A1": (1.00, 0.45, 0.05, 0.10),   # глубокий синий, Pantone 3015 C
    "#0EA5E9": (0.75, 0.15, 0.00, 0.00),   # небесный, Pantone 2995 C
    "#0F172A": (0.80, 0.65, 0.40, 0.80),   # чернильный
    "#FDE047": (0.00, 0.05, 0.80, 0.00),   # маркерный жёлтый (трендовая визитка «Маркер»)
    "#12365C": (1.00, 0.75, 0.35, 0.28),   # тон в тон к тёмно-синему (тот же цвет, K меньше): под выборочный лак
    "#000000": (0.00, 0.00, 0.00, 1.00),   # файл лака: только K 100%
}


def qr(url, x, y, size, color):
    q = segno.make(url, error="m")
    rows = list(q.matrix_iter(scale=1, border=0))
    cell = size / len(rows)
    d = "".join(f"M{x + c * cell:.3f} {y + r * cell:.3f}h{cell:.3f}v{cell:.3f}h-{cell:.3f}z"
                for r, row in enumerate(rows) for c, v in enumerate(row) if v)
    return f'<path d="{d}" fill="{color}"/>'


def txt(s, x, baseline, size, color, weight=600, anchor="start", tracking=0.0):
    return B.text(s, x, baseline, size, color, weight=weight, anchor=anchor, tracking=tracking)[0]


def doc(body, w=W, h=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
            f'{body}</svg>\n')


def front():
    logo, lw, lh = B.horizontal("color-dark", gid="cf")
    k = 58 / lw
    lx, ly = BLEED + (TRIM_W - lw * k) / 2, BLEED + 15.5
    return doc(
        f'<rect width="{W}" height="{H}" fill="{B.NAVY}"/>'
        f'<g transform="translate({lx:.3f},{ly:.3f}) scale({k:.5f})">{logo}</g>'
        + txt("Чисто. Точка.", BLEED + TRIM_W / 2, BLEED + 35.5, 4.0, B.SKY_ON_DARK, weight=800, anchor="middle")
        + txt("клининговая служба · Тюмень", BLEED + TRIM_W / 2, BLEED + 41.5, 2.5, MUTED_DARK, weight=600, anchor="middle",
              tracking=0.02))


def check(cx, cy, r=1.1, fill=B.SKY, tick="#FFFFFF"):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
            f'<path d="M{cx - r * .45},{cy + r * .02} l{r * .32},{r * .32} l{r * .6},{-r * .64}" fill="none" stroke="{tick}" '
            f'stroke-width="{r * .32:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')


def back_company():
    points = ["Цена до выезда", "Оплата после приёмки", "Переуберём за 24 часа", "Расчёт за 7 минут"]
    rows = "".join(check(X0 + 2.5 + 1.1, Y0 + 9.6 + i * 4.3 - 0.9) + txt(p, X0 + 2.5 + 3.4, Y0 + 9.6 + i * 4.3, 2.7, B.INK)
                   for i, p in enumerate(points))
    qs = 21.0
    qx, qy = X1 - qs, Y0
    return doc(
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>'
        f'<rect width="{BLEED + 2.5}" height="{H}" fill="{B.SKY}"/>'
        + txt("Уборка квартир в Тюмени", X0 + 2.5, Y0 + 3.6, 3.6, B.INK, weight=800)
        + rows
        + txt(PHONE, X0 + 2.5, Y1 - 7.6, 4.1, B.INK, weight=800)
        + txt(SITE, X0 + 2.5, Y1 - 3.3, 2.8, B.DEEP, weight=700)
        + txt(VK, X0 + 2.5, Y1, 2.5, B.MUTED, weight=600)
        + qr(QR_URL, qx, qy, qs, B.INK)
        + txt("Расчёт цены", qx + qs / 2, qy + qs + 3.4, 2.4, B.MUTED, weight=700, anchor="middle"))


def back_person(name, role, phone):
    qs = 19.0
    qx, qy = X1 - qs, Y0 + 1.0
    logo, lw, lh = B.horizontal("color", gid="cb")
    k = 30 / lw
    return doc(
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>'
        f'<rect width="{BLEED + 2.5}" height="{H}" fill="{B.SKY}"/>'
        f'<g transform="translate({X0 + 2.5:.3f},{Y0:.3f}) scale({k:.5f})">{logo}</g>'
        + txt(name, X0 + 2.5, Y0 + 15.5, 4.6, B.INK, weight=800)
        + txt(role, X0 + 2.5, Y0 + 20.4, 2.7, B.DEEP, weight=700)
        + txt(phone, X0 + 2.5, Y1 - 6.4, 3.8, B.INK, weight=800)
        + txt(f"{SITE}  ·  {VK}", X0 + 2.5, Y1 - 1.6, 2.4, B.MUTED, weight=600)
        + qr(QR_URL, qx, qy, qs, B.INK)
        + txt("Расчёт цены", qx + qs / 2, qy + qs + 3.2, 2.3, B.MUTED, weight=700, anchor="middle"))


# Дерзкие визитки-«перевёртыши»: на лице — провокация, на обороте — развязка и контакты.
# (ключ, строки лица, строки развязки, подстрочник развязки)
HOOKS = [
    ("bold-get-out", ["Убирайтесь"], ["…из дома."], "Вернётесь — будет чисто."),
    ("bold-drop-rag", ["Положите", "тряпку"], ["…и отойдите", "от раковины."], "Это работа для профессионалов."),
]


def drop_period(x_end, baseline, size, color):
    """Фирменная капля вместо точки после слова."""
    s = size * 0.46 / 17.2                       # капля в знаке: x 9.7–22.3, y 5.8–23.0 (единицы 32×32)
    x = x_end + size * 0.07 - 9.7 * s
    y = baseline - 23.0 * s
    return f'<g transform="translate({x:.3f},{y:.3f}) scale({s:.4f})"><path d="{B.DROP}" fill="{color}"/></g>'


def bubble(cx, cy, r):
    """Мыльный пузырь контуром: без прозрачности, чтобы печать не зависела от сведения слоёв."""
    w = max(0.22, r * 0.09)
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{B.SKY_ON_DARK}" stroke-width="{w:.2f}"/>'
            f'<path d="M{cx - r * .55:.2f},{cy - r * .1:.2f} A{r * .6:.2f},{r * .6:.2f} 0 0 1 {cx - r * .05:.2f},{cy - r * .6:.2f}" '
            f'fill="none" stroke="#FFFFFF" stroke-width="{w * 1.3:.2f}" stroke-linecap="round"/>')


def hook_front(lines):
    probe = max(B.text(t, 0, 0, 1, B.WHITE, weight=800)[1] for t in lines)
    size = min(16.0, 70.0 / probe)
    lh = size * 1.0
    logo, lw, lh_logo = B.horizontal("color-dark", gid="hf")
    k = 28 / lw
    block = size * 0.72 + (len(lines) - 1) * lh          # от верха прописных до последней базовой линии
    free_bottom = Y1 - lh_logo * k - 3.0                  # над логотипом
    first = max(BLEED + 8.5 + size * 0.72, Y0 + (free_bottom - Y0 - block) / 2 + size * 0.72)
    words = ""
    for i, t in enumerate(lines):
        base = first + i * lh
        words += txt(t, X0, base, size, B.WHITE, weight=800)
        if i == len(lines) - 1:
            words += drop_period(X0 + B.text(t, X0, base, size, B.WHITE, weight=800)[1], base, size, B.SKY)
    flip_y = Y1 - 0.6
    arrow = (f'<path d="M{X1 - 3.4},{flip_y - 2.6} a2.1,2.1 0 1 1 -0.4,3.2" fill="none" stroke="{B.SKY_ON_DARK}" '
             f'stroke-width="0.35" stroke-linecap="round"/>'
             f'<path d="M{X1 - 4.4},{flip_y + 0.3} l0.9,0.4 l0.2,-1" fill="none" stroke="{B.SKY_ON_DARK}" stroke-width="0.35" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')
    bubbles = "".join(bubble(x, y, r) for x, y, r in ((84.5, 8.4, 4.2), (77.0, 5.4, 1.6), (90.0, 16.4, 1.5)))
    return doc(
        f'<rect width="{W}" height="{H}" fill="{B.NAVY}"/>' + bubbles + words
        + f'<g transform="translate({X0:.3f},{Y1 - lh_logo * k:.3f}) scale({k:.5f})">{logo}</g>'
        + txt("переверните", X1 - 5.6, flip_y, 2.4, B.SKY_ON_DARK, weight=700, anchor="end") + arrow)


def hook_back(lines, sub):
    qs = 19.0
    qx, qy = X1 - qs, Y0
    colw = qx - 3.5 - (X0 + 2.5)
    probe = max(B.text(t, 0, 0, 1, B.INK, weight=800)[1] for t in lines)
    size = min(6.4, colw / probe)
    y = Y0 + size * 0.75
    out = ""
    for t in lines:
        out += txt(t, X0 + 2.5, y, size, B.INK, weight=800)
        y += size * 1.05
    out += txt(sub, X0 + 2.5, y + 0.4, 3.0, B.DEEP, weight=700)
    last = Y1 - 4.3 - 3.9 - 3.0                            # список заканчивается над телефоном с отступом 3 мм
    for i, p in enumerate(["Цена до выезда", "Оплата после приёмки", "Переуберём за 24 часа"]):
        yy = last - (2 - i) * 3.7
        out += check(X0 + 2.5 + 1.0, yy - 0.85, 1.0) + txt(p, X0 + 2.5 + 3.1, yy, 2.45, B.INK)
    return doc(
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>'
        f'<rect width="{BLEED + 2.5}" height="{H}" fill="{B.SKY}"/>'
        + out
        + txt(PHONE, X0 + 2.5, Y1 - 4.3, 3.9, B.INK, weight=800)
        + txt(f"{SITE}  ·  {VK}", X0 + 2.5, Y1, 2.3, B.MUTED, weight=600)
        + qr(QR_URL, qx, qy, qs, B.INK)
        + txt("Цена за 7 минут", qx + qs / 2, qy + qs + 3.2, 2.3, B.MUTED, weight=700, anchor="middle"))


# ——— Трендовые визитки: коллекционная серия, тактильный минимализм, яркий маркер ———
# Крупные слова — акцидентным Unbounded (SIL OFL), остальное — фирменным Manrope.

VW, VH = H, W                                        # вертикальная 50×90 мм, файл 54×94
VX0, VY0, VX1, VY1 = X0, Y0, BLEED + TRIM_H - SAFE, BLEED + TRIM_W - SAFE
YELLOW = "#FDE047"                                   # маркерный жёлтый
TONE = "#12365C"                                     # тон в тон к тёмно-синему: под выборочный лак
ART_DPI = 600
ART = {}                                             # имя → (SVG, ширина, высота): растровые слои иллюстраций


def qr_url(content):
    """Своя метка utm_content у каждого дизайна: в Метрике видно, какая визитка приводит заявки."""
    return f"{QR_URL}&utm_content={content}"


def disp(s, x, baseline, size, color, weight=900, anchor="start", tracking=0.0):
    return B.text(s, x, baseline, size, color, weight=weight, anchor=anchor, tracking=tracking, family="unbounded")[0]


def width(s, size, weight=600, family="manrope", tracking=0.0):
    return B.text(s, 0, 0, size, "#000", weight=weight, tracking=tracking, family=family)[1]


def art(name, body, w, h):
    """Иллюстрации — непрозрачной картинкой 600 dpi под векторным текстом: в предметах есть полупрозрачные
    градиенты, а в печать файл уходит без прозрачностей."""
    ART[name] = (doc(body, w, h), w, h)
    return f'<image href="{{art:{name}}}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="none"/>'


def slogan(x, baseline, size, color, dot, anchor="start", weight=900):
    """«Чисто. Точка.» с фирменными каплями вместо точек."""
    w1, w2 = width("Чисто", size, weight, "unbounded"), width("Точка", size, weight, "unbounded")
    gap, tail = size * 0.72, size * 0.45
    total = w1 + gap + w2 + tail
    x = {"start": x, "middle": x - total / 2, "end": x - total}[anchor]
    return (disp("Чисто", x, baseline, size, color, weight) + drop_period(x + w1, baseline, size, dot)
            + disp("Точка", x + w1 + gap, baseline, size, color, weight) + drop_period(x + w1 + gap + w2, baseline, size, dot)), total


def foam(x, y, r):
    """Пузырь из illustrations.py в миллиметрах (обводка предмета рассчитана на его собственные единицы)."""
    return I.g(x, y, r / 30, I.bubble(0, 0, 30))


# Серия из четырёх лиц с общим оборотом: (ключ, строки названия, услуга, цена, фон).
COLLECTION = [
    ("fresh", ["Свежо"], "поддерживающая уборка", "от 2 400 ₽", "#E0F2FE"),
    ("general", ["Генералка"], "генеральная уборка", "от 4 900 ₽", "#DCFCE7"),
    ("renovation", ["После", "ремонта"], "уборка после ремонта", "от 6 200 ₽", "#FEF3C7"),
    ("windows", ["Окна"], "мытьё окон без разводов", "350 ₽ за створку", "#E0E7FF"),
]


def scene(key):
    """Предметы из illustrations.py на светлом круге, координаты — миллиметры вертикальной визитки."""
    halo = f'<circle cx="{VW / 2}" cy="33.5" r="19.5" fill="#FFFFFF" opacity=".7"/>'
    if key == "fresh":
        things = (I.spray(12.5, 14.5, .165) + I.sponge(25.5, 37.5, .17, rotate=-8)
                  + foam(39, 21, 3.2) + foam(44, 28, 1.7) + foam(34.5, 15.5, 1.3)
                  + I.sparkle(41.5, 44, 1.6, I.SUN) + I.sparkle(9.5, 47, 1.1, I.SKY))
    elif key == "general":
        things = (I.bucket(7.5, 26.5, .17) + I.spray(31, 18, .15)
                  + foam(13, 18.5, 2.2) + foam(44.5, 16, 1.3)
                  + I.sparkle(23, 15, 1.7, I.SUN) + I.sparkle(46, 44, 1.2, I.SKY))
    elif key == "renovation":
        things = (I.bucket(7, 30.5, .15) + I.roller(24, 25.5, .155, rotate=-20)
                  + foam(14, 21, 1.8) + I.sparkle(42, 16.5, 1.7, I.SUN) + I.sparkle(10, 17, 1.1, I.SKY))
    else:
        things = (I.window(11.5, 14, 220, 260, .118) + I.squeegee(30, 33, .12, rotate=-18)
                  + I.sparkle(44, 17, 1.7, I.SUN) + I.sparkle(8.5, 45, 1.2, I.SKY))
    return halo + things


def collection_front(i, key, lines, sub, price, bg):
    n = len(COLLECTION)
    out = art(f"collection-{key}", f'<rect width="{VW}" height="{VH}" fill="{bg}"/>' + scene(key), VW, VH)
    num = f"{i:02d}"
    out += disp(num, VX0, VY0 + 2.2, 2.6, B.NAVY, weight=700)
    out += disp(f" / {n:02d}", VX0 + width(num, 2.6, 700, "unbounded"), VY0 + 2.2, 2.6, B.DEEP, weight=500)
    out += B.mark(VX1 - 5.2, VY0 - 1.0, 5.2, gid=f"cm{i}")
    # снизу вверх: подпись бренда, цена на плашке, услуга, название
    out += txt("Точка Чистоты · Тюмень", VX0, VY1, 2.2, B.MUTED, weight=700)
    ph, psize = 6.4, 2.7
    py = VY1 - 3.9 - ph
    pw = width(price, psize, 700, "unbounded") + 5.0
    out += f'<rect x="{VX0}" y="{py:.3f}" width="{pw:.3f}" height="{ph}" rx="{ph / 2}" fill="{B.NAVY}"/>'
    out += disp(price, VX0 + 2.5, py + ph / 2 + psize * 0.37, psize, B.WHITE, weight=700)
    sub_base = py - 2.8
    out += txt(sub, VX0, sub_base, 2.7, B.DEEP, weight=700)
    probe = max(width(t, 1, 900, "unbounded") for t in lines)
    size = min(7.6, (VX1 - VX0) / probe)
    lh = size * 1.02
    last = sub_base - 2.7 - 2.0
    for j, t in enumerate(lines):
        out += disp(t, VX0, last - (len(lines) - 1 - j) * lh, size, B.NAVY)
    return doc(out, VW, VH)


def collection_back():
    logo, lw, lh = B.stacked("color", gid="cbk")
    k = 27 / lw
    cx = VW / 2
    out = f'<rect width="{VW}" height="{VH}" fill="#FFFFFF"/>'
    out += f'<g transform="translate({cx - lw * k / 2:.3f},{VY0 + 0.6:.3f}) scale({k:.5f})">{logo}</g>'
    s, _ = slogan(cx, VY0 + lh * k + 8.0, 4.0, B.INK, B.SKY, anchor="middle")
    out += s
    points = ["Цена до выезда", "Оплата после приёмки", "Переуберём за 24 часа"]
    colw = max(width(p, 2.45) for p in points) + 3.1
    lx = cx - colw / 2
    top = VY0 + lh * k + 13.6
    for j, p in enumerate(points):
        y = top + j * 3.9
        out += check(lx + 1.0, y - 0.85, 1.0) + txt(p, lx + 3.1, y, 2.45, B.INK)
    qs = 21.0
    qy = top + 2 * 3.9 + 3.6
    out += qr(qr_url("collection"), cx - qs / 2, qy, qs, B.INK)
    out += txt("Цена за 7 минут", cx, qy + qs + 3.1, 2.3, B.MUTED, weight=700, anchor="middle")
    out += txt(PHONE, cx, VY1 - 8.2, 3.7, B.INK, weight=800, anchor="middle")
    out += txt(SITE, cx, VY1 - 3.9, 2.5, B.DEEP, weight=700, anchor="middle")
    out += txt(VK, cx, VY1, 2.3, B.MUTED, weight=600, anchor="middle")
    return doc(out, VW, VH)


def tactile_drop(fill):
    """Крупная капля знака, выходит за правый и нижний край; круг знака — над нижним обрезом."""
    s = 3.8
    tx, ty = 70.0 - 16 * s, 7.5 - 5.8 * s
    cx, cy, r = B.DOT
    return (f'<g transform="translate({tx:.3f},{ty:.3f}) scale({s})"><path d="{B.DROP}" fill="{fill}"/></g>',
            (tx + cx * s, ty + cy * s, r * s))


def tactile_front(mask=False):
    """Тёмно-синее лицо под soft-touch: капля тон в тон и надпись — под выборочный УФ-лак.
    mask=True — файл лака: чёрное лакируется, белое — нет."""
    bg, drop_c, dot_c = ("#FFFFFF", "#000000", "#000000") if mask else (B.NAVY, TONE, B.SKY)
    drop, (cx, cy, r) = tactile_drop(drop_c)
    c1, c2 = ("#000000", "#000000") if mask else (B.WHITE, B.SKY_ON_DARK)
    word, ww, cap = B.wordmark(X0, Y0 + 3.4, 4.6, c1, c2)
    out = f'<rect width="{W}" height="{H}" fill="{bg}"/>' + drop + f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{dot_c}"/>' + word
    if not mask:
        out += txt("клининг · Тюмень", X0, Y1, 2.4, MUTED_DARK, weight=600, tracking=0.04)
    return doc(out)


def tactile_back():
    qs = 17.0
    qx, qy = X1 - qs, Y0
    s, _ = slogan(X0, Y0 + 3.4, 4.6, B.INK, B.SKY)
    return doc(
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>' + s
        + txt("Уборка квартир в Тюмени.", X0, Y0 + 10.4, 2.6, B.MUTED, weight=600)
        + txt("Цена до выезда, оплата после приёмки.", X0, Y0 + 14.0, 2.6, B.MUTED, weight=600)
        + txt(PHONE, X0, Y1 - 4.6, 4.2, B.INK, weight=800)
        + txt(f"{SITE}  ·  {VK}", X0, Y1, 2.3, B.MUTED, weight=600)
        + qr(qr_url("tactile"), qx, qy, qs, B.INK)
        + txt("Цена за 7 минут", qx + qs / 2, qy + qs + 3.1, 2.2, B.MUTED, weight=700, anchor="middle"))


def marker_front():
    """Маркерный жёлтый и одно огромное слово, подчёркнутое небесным «маркером»."""
    logo, lw, lh = B.horizontal("color", gid="mf")
    k = 26 / lw
    word = "ЧИСТО"
    probe = width(word, 1, 900, "unbounded")
    size = (X1 - X0) / (probe + 0.45)
    base = Y1 - 8.6
    ww = probe * size
    cap = size * 0.75
    bar_y, bar_h = base - cap * 0.46, cap * 0.56
    bar = (f'<rect x="{X0 - 1.6:.3f}" y="{bar_y:.3f}" width="{ww + size * 0.45 + 3.2:.3f}" height="{bar_h:.3f}" rx="0.8" '
           f'fill="{B.SKY}" transform="rotate(-1.6 {X0 + ww / 2:.3f} {bar_y + bar_h / 2:.3f})"/>')
    return doc(
        f'<rect width="{W}" height="{H}" fill="{YELLOW}"/>'
        f'<g transform="translate({X0:.3f},{Y0:.3f}) scale({k:.5f})">{logo}</g>'
        + txt("Тюмень", X1, Y0 + 3.6, 2.6, B.NAVY, weight=800, anchor="end")
        + bar + disp(word, X0, base, size, B.NAVY) + drop_period(X0 + ww, base, size, B.NAVY)
        + txt("уборка квартир · цена за 7 минут", X0, Y1, 2.9, B.NAVY, weight=800))


def marker_back():
    plate, pad = 21.0, 2.0
    px, py = X1 - plate, Y0
    colw = px - 3.0 - X0
    lines = [("Пыль — наша.", B.NAVY), ("Время — ваше.", B.WHITE)]
    probe = max(width(t, 1, 900, "unbounded") for t, _ in lines)
    size = min(5.0, colw / probe)
    out = "".join(disp(t, X0, Y0 + size * 0.75 + j * size * 1.12, size, c) for j, (t, c) in enumerate(lines))
    top = Y0 + size * 0.75 + size * 1.12 + 6.0
    for j, p in enumerate(["Цена до выезда", "Оплата после приёмки", "Переуберём за 24 часа"]):
        y = top + j * 3.8
        out += check(X0 + 1.0, y - 0.85, 1.0, fill=B.NAVY) + txt(p, X0 + 3.1, y, 2.45, B.NAVY, weight=700)
    ph, psize = 7.2, 3.8
    pill_y = Y1 - 4.0 - ph
    pw = width(PHONE, psize, 800) + 5.6
    out += f'<rect x="{X0}" y="{pill_y:.3f}" width="{pw:.3f}" height="{ph}" rx="{ph / 2}" fill="{YELLOW}"/>'
    out += txt(PHONE, X0 + 2.8, pill_y + ph / 2 + psize * 0.36, psize, B.NAVY, weight=800)
    out += txt(f"{SITE}  ·  {VK}", X0, Y1, 2.3, B.NAVY, weight=700)
    out += f'<rect x="{px}" y="{py}" width="{plate}" height="{plate}" rx="2.2" fill="#FFFFFF"/>'
    out += qr(qr_url("marker"), px + pad, py + pad, plate - 2 * pad, B.NAVY)
    out += txt("Цена за 7 минут", px + plate / 2, py + plate + 3.2, 2.3, B.NAVY, weight=700, anchor="middle")
    return doc(f'<rect width="{W}" height="{H}" fill="{B.SKY}"/>' + out)


def card(key, front_svg, back_svg, title, w=W, h=H, preview=None, mask=None, radius=0.0):
    """Визитка для сборки. preview — общее превью серии; mask — лицо под выборочный лак; radius — скругление углов
    в превью (сам макет не меняет: скругляет типография, в безопасную зону 4 мм радиус до 4 мм не заходит)."""
    return dict(key=key, front=front_svg, back=back_svg, title=title, w=w, h=h, preview=preview or key, mask=mask,
                radius=radius)


def trend_cards():
    back = collection_back()
    cards = [card(f"collection-{i:02d}-{key}", collection_front(i, key, lines, sub, price, bg), back,
                  f"Коллекция {i}/{len(COLLECTION)}: «{' '.join(lines)}»", w=VW, h=VH, preview="collection", radius=3.0)
             for i, (key, lines, sub, price, bg) in enumerate(COLLECTION, 1)]
    cards.append(card("tactile", tactile_front(), tactile_back(), "Тактильная: soft-touch и выборочный лак",
                      mask=tactile_front(mask=True), radius=3.0))
    cards.append(card("marker", marker_front(), marker_back(), "Яркая: маркер"))
    return cards


def gs_cmyk(src, dst):
    # картинки иллюстраций — без пережатия в JPEG и без понижения разрешения
    subprocess.run(["gs", "-q", "-o", dst, "-sDEVICE=pdfwrite", "-sColorConversionStrategy=CMYK",
                    "-sProcessColorModel=DeviceCMYK", "-dPDFSETTINGS=/prepress", "-dCompressPages=false",
                    "-dDownsampleColorImages=false", "-dAutoFilterColorImages=false", "-sColorImageFilter=FlateEncode",
                    src], check=True)


def calibrate(tmp):
    """Во что Ghostscript переводит каждый фирменный цвет: те же Chromium и gs, что и для визиток."""
    order = list(BRAND_CMYK)
    rects = "".join(f'<rect x="{i * 10}" y="0" width="10" height="10" fill="{c}"/>' for i, c in enumerate(order))
    svg = os.path.join(tmp, "calib.svg")
    with open(svg, "w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{10 * len(order)}mm" height="10mm" '
                f'viewBox="0 0 {10 * len(order)} 10">{rects}</svg>')
    mpath = os.path.join(tmp, "calib.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump([{"svg": svg, "pdf": {"file": os.path.join(tmp, "calib.pdf"), "width_mm": 10 * len(order)}}], f)
    subprocess.run(["node", os.path.join(TOOLS, "render.js"), mpath], check=True)
    gs_cmyk(os.path.join(tmp, "calib.pdf"), os.path.join(tmp, "calib-cmyk.pdf"))
    seen = []
    for stream in _streams(PdfReader(os.path.join(tmp, "calib-cmyk.pdf")).pages[0]):
        for m in re.finditer(r"([\d.]+ [\d.]+ [\d.]+ [\d.]+) k\b", stream.get_data().decode("latin-1")):
            if m.group(1) not in seen:
                seen.append(m.group(1))
    if len(seen) != len(order):
        raise RuntimeError(f"калибровка CMYK: ожидалось {len(order)} цветов, найдено {seen}")
    return {gs_value: "{:.2f} {:.2f} {:.2f} {:.2f}".format(*BRAND_CMYK[c]) for gs_value, c in zip(seen, order)}


def _streams(page, with_contents=True):
    """Поток страницы (по желанию) и все вложенные Form XObject."""
    out = [page.get_contents()] if with_contents else []
    todo = [page.get("/Resources")]
    while todo:
        res = todo.pop()
        res = res.get_object() if res is not None else None
        if not res or "/XObject" not in res:
            continue
        for ref in res["/XObject"].get_object().values():
            obj = ref.get_object()
            if obj.get("/Subtype") == "/Form":
                out.append(obj)
                todo.append(obj.get("/Resources"))
    return out


def to_cmyk(src, dst, mapping):
    """RGB → CMYK через Ghostscript, затем плашки бренда получают точные CMYK из гайда."""
    gs_cmyk(src, dst)
    writer = PdfWriter(clone_from=dst)
    pattern = re.compile(r"([\d.]+ [\d.]+ [\d.]+ [\d.]+) (k|K)\b")

    def fix(data: bytes) -> bytes:
        text = data.decode("latin-1")
        return pattern.sub(lambda m: f"{mapping.get(m.group(1), m.group(1))} {m.group(2)}", text).encode("latin-1")

    for page in writer.pages:
        contents = page.get_contents()
        contents.set_data(fix(contents.get_data()))
        page.replace_contents(contents)
        for xobj in _streams(page, with_contents=False):
            xobj.set_data(fix(xobj.get_data()))
    with open(dst, "wb") as f:
        writer.write(f)


def set_boxes(path, w=W, h=H):
    """Страница — ровно w×h мм от верхнего края (Chromium округляет размер вверх), TrimBox — на 2 мм внутрь."""
    mm = 72 / 25.4
    reader, writer = PdfReader(path), PdfWriter()
    for page in reader.pages:
        top = float(page.mediabox.top)
        box = RectangleObject([0, top - h * mm, w * mm, top])
        page.mediabox = box
        page.cropbox = box
        page.bleedbox = box
        page.trimbox = RectangleObject([BLEED * mm, top - (h - BLEED) * mm, (w - BLEED) * mm, top - BLEED * mm])
        writer.add_page(page)
    with open(path, "wb") as f:
        writer.write(f)


def bake_art(tmp, cards):
    """Растровые слои: рендер 600 dpi, RGB без альфа-канала, в SVG сторон — data URI."""
    if not ART:
        return
    from PIL import Image
    manifest = []
    for name, (svg, w, h) in ART.items():
        p = os.path.join(tmp, f"art-{name}.svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        manifest.append({"svg": p, "png": [{"file": p[:-4] + ".png", "width": round(w / 25.4 * ART_DPI), "bg": "#FFFFFF"}]})
    mpath = os.path.join(tmp, "art.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    subprocess.run(["node", os.path.join(TOOLS, "render.js"), mpath], check=True)
    uris = {}
    for name in ART:
        buf = io.BytesIO()
        Image.open(os.path.join(tmp, f"art-{name}.png")).convert("RGB").save(buf, "PNG", optimize=True)
        uris[name] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    for c in cards:
        for side in ("front", "back"):
            c[side] = re.sub(r"\{art:([\w-]+)\}", lambda m: uris[m.group(1)], c[side])


def trim_name(c):
    return f"{round(c['w'] - 2 * BLEED)}x{round(c['h'] - 2 * BLEED)}mm"


def sheet(images, gap=40, bg="#E9EEF3"):
    from PIL import Image
    width = sum(im.width for im in images) + gap * (len(images) + 1)
    height = max(im.height for im in images) + gap * 2
    out = Image.new("RGB", (width, height), bg)
    x = gap
    for im in images:
        out.paste(im, (x, gap + (height - 2 * gap - im.height) // 2), im if im.mode == "RGBA" else None)
        x += im.width + gap
    return out


def build():
    from PIL import Image, ImageDraw
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    cards = [card("company", front(), back_company(), "Общая визитка компании")]
    cards += [card(f"person-{key}", front(), back_person(name, role, phone), f"Именная: {name}, {role}")
              for key, name, role, phone in PEOPLE]
    cards += [card(key, hook_front(face), hook_back(punch, sub), f"Дерзкая: «{' '.join(face)}»") for key, face, punch, sub in HOOKS]
    cards += trend_cards()
    bake_art(tmp, cards)

    manifest = []
    for c in cards:
        for side in ("front", "back", "mask"):
            if not c[side]:
                continue
            p = os.path.join(tmp, f"{c['key']}-{side}.svg")
            with open(p, "w", encoding="utf-8") as f:
                f.write(c[side])
            item = {"svg": p, "pdf": {"file": p[:-4] + ".pdf", "width_mm": c["w"]}}
            if side != "mask":
                item["png"] = [{"file": p[:-4] + ".png", "width": round(c["w"] * PREVIEW_PX), "bg": "#FFFFFF"}]
            manifest.append(item)
    mpath = os.path.join(tmp, "manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    subprocess.run(["node", os.path.join(TOOLS, "render.js"), mpath], check=True)
    mapping = calibrate(tmp) if shutil.which("gs") else None

    def finish(pages, final, c):
        writer = PdfWriter()
        for p in pages:
            writer.append(p)
        rgb = final + ".rgb.pdf"
        with open(rgb, "wb") as f:
            writer.write(f)
        if mapping:
            to_cmyk(rgb, final, mapping)
        else:
            shutil.copy(rgb, final)
        os.remove(rgb)
        set_boxes(final, c["w"], c["h"])
        made.add(os.path.basename(final))

    made, previews = {"README.md"}, {}
    for c in cards:
        side_pdf = lambda side: os.path.join(tmp, f"{c['key']}-{side}.pdf")  # noqa: E731
        finish([side_pdf("front"), side_pdf("back")], os.path.join(OUT, f"card-{c['key']}_{trim_name(c)}_bleed2mm.pdf"), c)
        if c["mask"]:
            finish([side_pdf("mask")], os.path.join(OUT, f"card-{c['key']}_{trim_name(c)}_bleed2mm_spot-uv-front.pdf"), c)
        # превью без вылетов; у серии общий оборот показывается один раз
        group = previews.setdefault(c["preview"], {"front": [], "back": [], "seen": set()})
        for side in ("front", "back"):
            if c[side] in group["seen"]:
                continue
            group["seen"].add(c[side])
            b = round(BLEED * PREVIEW_PX)
            im = Image.open(os.path.join(tmp, f"{c['key']}-{side}.png")).convert("RGB")
            im = im.crop((b, b, im.width - b, im.height - b))
            if c["radius"]:
                m = Image.new("L", im.size, 0)
                ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=round(c["radius"] * PREVIEW_PX), fill=255)
                im.putalpha(m)
            group[side].append(im)
    for group in previews.values():
        group["images"] = group["front"] + group["back"]           # у серии: все лица, затем оборот
    for name, group in previews.items():
        sheet(group["images"]).save(os.path.join(OUT, f"card-{name}_preview.png"))
        made.add(f"card-{name}_preview.png")
    # обзор трендовых визиток одной картинкой: серия сверху, под ней тактильная и яркая
    rows = [sheet(previews[n]["images"]) for n in ("collection", "tactile", "marker")]
    overview = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), "#E9EEF3")
    y = 0
    for r in rows:
        overview.paste(r, ((overview.width - r.width) // 2, y))
        y += r.height
    overview.save(os.path.join(OUT, "trends_preview.png"))
    made.add("trends_preview.png")
    for f in os.listdir(OUT):
        if f not in made and os.path.isfile(os.path.join(OUT, f)):
            os.remove(os.path.join(OUT, f))
    shutil.rmtree(tmp)
    print(f"{len(cards)} визиток → {OUT}")


if __name__ == "__main__":
    build()
