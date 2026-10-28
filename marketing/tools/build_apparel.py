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
    with open(os.path.join(ROOT, "files.json"), "w", encoding="utf-8") as f:
        json.dump([{"file": n, "width_mm": wm, "height_mm": hm, "purpose": p} for n, wm, hm, p in index], f,
                  ensure_ascii=False, indent=1)
    print(f"{len(index)} печатных файлов → {ROOT}")


if __name__ == "__main__":
    build()
