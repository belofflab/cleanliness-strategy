"""Печатные файлы для формы: SVG и векторный PDF в масштабе 1:1 (мм), текст в кривых.

    python3 marketing/tools/build_apparel.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import segno

sys.path.insert(0, os.path.dirname(__file__))
import brandkit as B  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apparel"))
SVG, PDF, PNG = (os.path.join(ROOT, d) for d in ("svg", "pdf", "preview"))

# QR на спине ведёт на тюменский сайт с UTM, чтобы считать заявки «с формы».
QR_URL = "https://tyumen.cleanliness.pro/?utm_source=uniform&utm_medium=offline&utm_campaign=tyumen"


def qr_path(url: str, x: float, y: float, size: float) -> tuple[str, float]:
    qr = segno.make(url, error="m")
    rows = list(qr.matrix_iter(scale=1, border=0))
    n = len(rows)
    cell = size / n
    d = []
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v:
                d.append(f"M{x + c * cell:.3f} {y + r * cell:.3f}h{cell:.3f}v{cell:.3f}h-{cell:.3f}z")
    return "".join(d), cell


def back_print(scheme: str, with_qr: bool):
    """Спина: вертикальный логотип, подпись, сайт и (опционально) QR с призывом."""
    body, w, h = B.stacked(scheme, m=140, descriptor="клининговая служба", extra="cleanliness.pro")
    parts = [body]
    height = h
    if with_qr:
        color = B.SCHEMES[scheme][2]
        qsize = w * 0.36
        top = height + w * 0.08
        cta, _, _, _ = B.text("Закажите уборку", w / 2, top + w * 0.05, w * 0.07, color, weight=700, anchor="middle")
        qtop = top + w * 0.11
        d, cell = qr_path(QR_URL, w / 2 - qsize / 2, qtop, qsize)
        if scheme == "1c-white":
            # На тёмной ткани печатаем белую плашку, модули QR — вырез: тёмные на светлом читаются любой камерой.
            q = cell * 4
            x0, y0, side = w / 2 - qsize / 2 - q, qtop - q, qsize + 2 * q
            r = cell * 2
            plate = (f"M{x0 + r:.3f} {y0:.3f}h{side - 2 * r:.3f}a{r:.3f} {r:.3f} 0 0 1 {r:.3f} {r:.3f}"
                     f"v{side - 2 * r:.3f}a{r:.3f} {r:.3f} 0 0 1 -{r:.3f} {r:.3f}h-{side - 2 * r:.3f}"
                     f"a{r:.3f} {r:.3f} 0 0 1 -{r:.3f} -{r:.3f}v-{side - 2 * r:.3f}a{r:.3f} {r:.3f} 0 0 1 {r:.3f} -{r:.3f}z")
            parts += [cta, f'<path d="{plate}{d}" fill="{color}" fill-rule="evenodd"/>']
            height = y0 + side
        else:
            parts += [cta, f'<path d="{d}" fill="{color}"/>']
            height = qtop + qsize + cell * 4  # тихая зона QR внутри макета
    return "".join(parts), w, height



def slogan_back(lines, sub=None):
    """Спина: крупный слоган в одну краску, под ним горизонтальный логотип. Ширина макета — 1000 единиц."""
    W = 1000.0
    probe = max(B.text(t, 0, 0, 100, B.WHITE, weight=800)[1] for t in lines)
    size = min(190.0, 100 * W * 0.98 / probe)
    parts, y = [], 0.0
    for t in lines:
        y += size * 0.98
        parts.append(B.text(t, W / 2, y, size, B.WHITE, weight=800, anchor="middle")[0])
        y += size * 0.12
    if sub:
        y += size * 0.42
        parts.append(B.text(sub, W / 2, y, size * 0.3, B.WHITE, weight=600, anchor="middle")[0])
    logo, lw, lh = B.horizontal("1c-white")
    k = W * 0.4 / lw
    top = y + min(size * 0.45, 70.0)
    parts.append(f'<g transform="translate({W / 2 - lw * k / 2:.2f},{top:.2f}) scale({k:.4f})">{logo}</g>')
    return "".join(parts), W, top + lh * k


def rounded(x, y, w, h, r, fill, stroke=None, sw=0.0):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"{st} fill="{fill}"/>'


def chevron(title_lines, stripes):
    """Шеврон грейда на рукав: тканая нашивка на липучке, 90×40 мм (единицы = мм). Полосы — уровень грейда."""
    W, H = 90.0, 40.0
    parts = [rounded(1, 1, W - 2, H - 2, 7, B.NAVY, B.WHITE, 1.6)]
    parts.append(f'<g transform="translate(6,8) scale({18 / 32:.4f})">{B.mark(0, 0, 32, "onecolor", color=B.WHITE)}</g>')
    y = 15.5 if len(title_lines) == 2 else 19.5
    for t in title_lines:
        parts.append(B.text(t.upper(), 29, y, 6.0, B.WHITE, weight=800, tracking=0.03)[0])
        y += 7.6
    for i in range(stripes):
        parts.append(rounded(29 + i * 11, 30.5, 9, 3, 1.5, B.SKY))
    return "".join(parts), W, H


def name_patch(name):
    """Нашивка с именем на липучке, грудь справа: 100×25 мм (единицы = мм)."""
    W, H = 100.0, 25.0
    parts = [rounded(1, 1, W - 2, H - 2, 6, B.NAVY, B.WHITE, 1.4)]
    parts.append(f'<g transform="translate(6,4.5) scale({16 / 32:.4f})">{B.mark(0, 0, 32, "onecolor", color=B.WHITE)}</g>')
    parts.append(B.text(name, 60, 16.8, 11.5, B.WHITE, weight=800, anchor="middle")[0])
    return "".join(parts), W, H


def badge():
    """Бейдж 86×54 мм (формат банковской карты), полноцвет на ПВХ. Поля в [скобках] заполняются на каждого."""
    W, H = 86.0, 54.0
    logo, lw, lh = B.horizontal("1c-white")
    k = 30 / lw
    parts = [f'<defs><clipPath id="bc"><rect width="{W}" height="{H}" rx="3.5"/></clipPath></defs>',
             f'<g clip-path="url(#bc)"><rect width="{W}" height="{H}" fill="#FFFFFF"/><rect width="{W}" height="12" fill="{B.NAVY}"/>'
             f'<rect y="{H - 3}" width="{W}" height="3" fill="{B.SKY}"/></g>',
             f'<g transform="translate(5,{6 - lh * k / 2:.2f}) scale({k:.4f})">{logo}</g>',
             B.text("клининговая служба", W - 5, 7.4, 2.6, "#B6C3D3", weight=600, anchor="end")[0],
             rounded(5, 16, 22, 29, 2, "#E2EAF2"),
             '<circle cx="16" cy="26" r="5" fill="#B8C7D6"/><path d="M8,41 Q16,30 24,41Z" fill="#B8C7D6"/>',
             B.text("фото 3×4", 16, 44, 2.2, "#6B7A8F", weight=600, anchor="middle")[0],
             B.text("[Имя Фамилия]", 31, 21.5, 4.6, B.INK, weight=800)[0],
             B.text("[Грейд: старший клинер]", 31, 27.5, 3.2, B.DEEP, weight=700)[0],
             B.text("Аттестация: [месяц, год]", 31, 33.5, 2.7, "#44546A", weight=600)[0],
             B.text("Документы проверены", 31, 38.2, 2.7, "#44546A", weight=600)[0],
             B.text("Проверить сотрудника:", 31, 44.2, 2.4, "#6B7A8F", weight=600)[0],
             B.text("[телефон офиса]", 31, 48.2, 2.9, B.INK, weight=800)[0]]
    return "".join(parts), W, H


def doc_mm(body: str, w: float, h: float, width_mm: float, title: str) -> tuple[str, float]:
    height_mm = width_mm * h / w
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.2f}mm" height="{height_mm:.2f}mm" '
           f'viewBox="0 0 {w:.3f} {h:.3f}"><title>{title}</title>{body}</svg>\n')
    return svg, height_mm


ITEMS = [
    # (файл, функция → (body, w, h), ширина мм, на какой ткани, назначение)
    ("tshirt-chest_color_light", lambda: B.horizontal("color"), 90, "light", "Футболка/свитшот, грудь слева. DTF, светлая ткань"),
    ("tshirt-chest_white_dark", lambda: B.horizontal("1c-white"), 90, "dark", "Футболка/свитшот, грудь слева. Шелкография/DTF, тёмная ткань"),
    ("tshirt-back_color_light", lambda: back_print("color", True), 260, "light", "Футболка/худи, спина с QR. DTF, светлая ткань"),
    ("tshirt-back_white_dark", lambda: back_print("1c-white", True), 260, "dark", "Футболка/худи/куртка, спина с QR. Шелкография/DTF, тёмная ткань"),
    ("tshirt-back-noqr_white_dark", lambda: back_print("1c-white", False), 240, "dark", "Спина без QR (для любого города)"),
    ("polo-embroidery_white_dark", lambda: B.horizontal("1c-white"), 80, "dark", "Поло, вышивка грудь слева, нить белая"),
    ("polo-embroidery_blue_light", lambda: B.horizontal("1c-blue"), 80, "light", "Поло, вышивка грудь слева, нить синяя"),
    ("cap-front_white_dark", lambda: (B.mark(0, 0, 32, "onecolor", color=B.WHITE), 32, 32), 50, "dark", "Кепка, перед. Вышивка белым"),
    ("sleeve_white_dark", lambda: (B.mark(0, 0, 32, "onecolor", color=B.WHITE), 32, 32), 70, "dark", "Рукав. Шелкография/DTF белым"),
    ("apron-chest_white_dark", lambda: B.stacked("1c-white", descriptor="клининговая служба"), 170, "dark", "Фартук, грудь. Шелкография белым"),
    ("apron-chest_color_light", lambda: B.stacked("color", descriptor="клининговая служба"), 170, "light", "Фартук светлый, грудь. DTF"),
    # Слоганы на спину футболки (внутри квартиры клиент видит спину клинера чаще всего). Для XS–S — 240 мм.
    ("back-slogan-tochka_white_dark", lambda: slogan_back(["Чисто.", "Точка."]), 280, "dark",
     "Спина футболки: слоган «Чисто. Точка.» Шелкография белым"),
    ("back-slogan-dust_white_dark", lambda: slogan_back(["Беру пыль", "на себя"]), 280, "dark",
     "Спина футболки: слоган «Беру пыль на себя». Шелкография белым"),
    ("back-slogan-guarantee_white_dark", lambda: slogan_back(["Не понравится —", "переуберу"], "бесплатно, в течение 24 часов"),
     280, "dark", "Спина футболки: гарантия переуборки. Шелкография белым"),
    ("back-slogan-weekend_white_dark", lambda: slogan_back(["Ваш выходной —", "моя работа"]), 280, "dark",
     "Спина футболки: слоган «Ваш выходной — моя работа». Шелкография белым"),
    # Знаки статуса и доверия: грейды — по лестнице аттестации (strategy/docs/appendix-a-standards.md, A7).
    ("chevron-certified_full", lambda: chevron(["Аттестованный", "клинер"], 1), 90, "dark",
     "Шеврон на левый рукав, грейд «Клинер» (после аттестации). Тканый, на липучке"),
    ("chevron-senior_full", lambda: chevron(["Старший", "клинер"], 2), 90, "dark",
     "Шеврон на левый рукав, грейд «Старший клинер». Тканый, на липучке"),
    ("chevron-lead_full", lambda: chevron(["Бригадир"], 3), 90, "dark",
     "Шеврон на левый рукав, грейд «Бригадир». Тканый, на липучке"),
    ("name-patch-sample_full", lambda: name_patch("Анна"), 100, "dark",
     "Нашивка с именем, грудь справа, на липучке. Образец: имя меняется на каждого сотрудника"),
    ("badge-template_full", badge, 86, "light",
     "Бейдж 86×54 мм на ПВХ-карте, полноцвет. Поля в [скобках] — на каждого сотрудника"),
    ("reflective-hood_silver_dark", lambda: (B.mark(0, 0, 32, "onecolor", color="#C3CBD5"), 32, 32), 70, "dark",
     "Капюшон худи / спина жилета: знак световозвращающей термоплёнкой (серебро)"),
]


def build():
    manifest, index = [], []
    for name, fn, width_mm, ground, purpose in ITEMS:
        body, w, h = fn()
        svg, height_mm = doc_mm(body, w, h, width_mm, f"Точка Чистоты — {name}")
        fname = f"{name}_{width_mm}x{round(height_mm)}mm"
        os.makedirs(SVG, exist_ok=True)
        path = os.path.join(SVG, f"{fname}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        bg = B.NAVY if ground == "dark" else "#FFFFFF"
        manifest.append({"svg": path,
                         "png": [{"file": os.path.join(PNG, f"{fname}.png"), "width": 900, "bg": bg}],
                         "pdf": {"file": os.path.join(PDF, f"{fname}.pdf"), "width_mm": width_mm}})
        index.append((fname, width_mm, round(height_mm), purpose))
    mpath = os.path.join(ROOT, "render-manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render.js"), mpath], check=True)
    os.remove(mpath)
    current = {n for n, *_ in index}
    for folder in (SVG, PDF, PNG):  # убрать файлы прежних версий: размер в имени мог измениться
        for f in os.listdir(folder):
            if os.path.splitext(f)[0] not in current:
                os.remove(os.path.join(folder, f))
    with open(os.path.join(ROOT, "files.json"), "w", encoding="utf-8") as f:
        json.dump([{"file": n, "width_mm": wm, "height_mm": hm, "purpose": p} for n, wm, hm, p in index], f,
                  ensure_ascii=False, indent=1)
    print(f"{len(index)} печатных файлов → {ROOT}")


if __name__ == "__main__":
    build()
