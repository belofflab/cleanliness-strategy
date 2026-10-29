"""Визитки под печать: 90×50 мм, вылеты 2 мм (файл 94×54 мм), текст в кривых, двусторонний PDF в CMYK.

    python3 marketing/tools/build_cards.py      → marketing/print/business-cards/

Общая визитка компании печатается как есть. Именные собираются из списка PEOPLE ниже: впишите имя, должность
и телефон сотрудника и перезапустите скрипт. Контакты Тюмени — из apps/web/lib/city.ts.
Для перевода в CMYK нужен Ghostscript (gs); без него остаётся RGB-PDF, и в CMYK переводит типография.
"""

from __future__ import annotations

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


def doc(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
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


def check(cx, cy, r=1.1):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{B.SKY}"/>'
            f'<path d="M{cx - r * .45},{cy + r * .02} l{r * .32},{r * .32} l{r * .6},{-r * .64}" fill="none" stroke="#FFFFFF" '
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


def gs_cmyk(src, dst):
    subprocess.run(["gs", "-q", "-o", dst, "-sDEVICE=pdfwrite", "-sColorConversionStrategy=CMYK",
                    "-sProcessColorModel=DeviceCMYK", "-dPDFSETTINGS=/prepress", "-dCompressPages=false", src], check=True)


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


def set_boxes(path):
    """Страница — ровно 94×54 мм от верхнего края (Chromium округляет размер вверх), TrimBox — на 2 мм внутрь."""
    mm = 72 / 25.4
    reader, writer = PdfReader(path), PdfWriter()
    for page in reader.pages:
        top = float(page.mediabox.top)
        box = RectangleObject([0, top - H * mm, W * mm, top])
        page.mediabox = box
        page.cropbox = box
        page.bleedbox = box
        page.trimbox = RectangleObject([BLEED * mm, top - (H - BLEED) * mm, (W - BLEED) * mm, top - BLEED * mm])
        writer.add_page(page)
    with open(path, "wb") as f:
        writer.write(f)


def build():
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    cards = [("company", front(), back_company(), "Общая визитка компании")]
    cards += [(f"person-{key}", front(), back_person(name, role, phone), f"Именная: {name}, {role}") for key, name, role, phone in PEOPLE]
    cards += [(key, hook_front(face), hook_back(punch, sub), f"Дерзкая: «{' '.join(face)}»") for key, face, punch, sub in HOOKS]
    manifest, index = [], []
    for key, f_svg, b_svg, title in cards:
        for side, svg in (("front", f_svg), ("back", b_svg)):
            p = os.path.join(tmp, f"{key}-{side}.svg")
            with open(p, "w", encoding="utf-8") as f:
                f.write(svg)
            manifest.append({"svg": p, "png": [{"file": os.path.join(tmp, f"{key}-{side}.png"), "width": 1128, "bg": "#FFFFFF"}],
                             "pdf": {"file": os.path.join(tmp, f"{key}-{side}.pdf"), "width_mm": W}})
        index.append((key, title))
    mpath = os.path.join(tmp, "manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    subprocess.run(["node", os.path.join(TOOLS, "render.js"), mpath], check=True)
    mapping = calibrate(tmp) if shutil.which("gs") else None

    from PIL import Image
    px = 1128 / W
    for key, _ in index:
        writer = PdfWriter()
        for side in ("front", "back"):
            writer.append(os.path.join(tmp, f"{key}-{side}.pdf"))
        rgb = os.path.join(tmp, f"{key}-rgb.pdf")
        with open(rgb, "wb") as f:
            writer.write(f)
        final = os.path.join(OUT, f"card-{key}_90x50mm_bleed2mm.pdf")
        if mapping:
            to_cmyk(rgb, final, mapping)
        else:
            shutil.copy(rgb, final)
        set_boxes(final)
        # превью без вылетов: лицо и оборот рядом
        sides = [Image.open(os.path.join(tmp, f"{key}-{s}.png")).crop((round(BLEED * px), round(BLEED * px),
                                                                     round((W - BLEED) * px), round((H - BLEED) * px)))
                 for s in ("front", "back")]
        gap = 40
        sheet = Image.new("RGB", (sides[0].width * 2 + gap * 3, sides[0].height + gap * 2), "#E9EEF3")
        for i, im in enumerate(sides):
            sheet.paste(im, (gap + i * (im.width + gap), gap))
        sheet.save(os.path.join(OUT, f"card-{key}_preview.png"))
    shutil.rmtree(tmp)
    print(f"{len(index)} визиток → {OUT}")


if __name__ == "__main__":
    build()
