"""Сборка логотипов: SVG в кривых → PNG и векторный PDF.

    python3 marketing/tools/build_brand.py     (нужны fonttools, brotli, uharfbuzz и Playwright)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import brandkit as B  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "brand"))
SVG, PNG, PDF = (os.path.join(ROOT, d) for d in ("svg", "png", "pdf"))

DESCRIPTOR = "клининговая служба"


def write(name: str, body: str, w: float, h: float, pad_ratio: float = 0.06, bg: str | None = None):
    pad = max(w, h) * pad_ratio
    os.makedirs(SVG, exist_ok=True)
    path = os.path.join(SVG, f"{name}.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(B.svg_doc(body, w, h, pad=pad, bg=bg, title=f"Точка Чистоты — {name}"))
    return path


def build():
    manifest = []

    def add(name, body, w, h, png_width=2000, pdf_mm=120, bg=None, dark_preview=False, pad_ratio=0.06):
        path = write(name, body, w, h, pad_ratio=pad_ratio, bg=bg)
        pngs = [{"file": os.path.join(PNG, f"{name}.png"), "width": png_width}]
        if dark_preview:
            pngs.append({"file": os.path.join(PNG, f"{name}_preview-on-navy.png"), "width": 1200, "bg": B.NAVY})
        manifest.append({"svg": path, "png": pngs, "pdf": {"file": os.path.join(PDF, f"{name}.pdf"), "width_mm": pdf_mm}})

    # Горизонтальные
    for scheme in ("color", "color-dark", "1c-blue", "1c-white", "1c-black"):
        body, w, h = B.horizontal(scheme)
        add(f"logo-horizontal_{scheme}", body, w, h, dark_preview=scheme in ("color-dark", "1c-white"))
    for scheme in ("color", "color-dark"):
        body, w, h = B.horizontal(scheme, descriptor=DESCRIPTOR)
        add(f"logo-horizontal-descriptor_{scheme}", body, w, h, dark_preview=scheme == "color-dark")

    # Вертикальные
    for scheme in ("color", "color-dark", "1c-blue", "1c-white"):
        body, w, h = B.stacked(scheme, descriptor=DESCRIPTOR)
        add(f"logo-stacked_{scheme}", body, w, h, png_width=1600, pdf_mm=90,
            dark_preview=scheme in ("color-dark", "1c-white"))

    # Знак
    for scheme, (variant, color) in {"color": ("color", None), "1c-blue": ("onecolor", B.DEEP),
                                     "1c-white": ("onecolor", B.WHITE), "1c-black": ("onecolor", B.INK)}.items():
        add(f"logo-mark_{scheme}", B.mark(0, 0, 32, variant, color=color), 32, 32, png_width=1024, pdf_mm=40,
            dark_preview=scheme == "1c-white")

    # Аватар сообщества VK: круглая обрезка, знак на всю площадь
    gid = "vk-grad"
    s = 1000 / 32
    avatar = (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1000" y2="1000" gradientUnits="userSpaceOnUse">'
              f'<stop stop-color="{B.SKY}"/><stop offset="1" stop-color="{B.DEEP}"/></linearGradient></defs>'
              f'<rect width="1000" height="1000" fill="url(#{gid})"/>'
              f'<g transform="translate(500 520) scale({s * 0.9:.4f}) translate(-16 -16)">'
              f'<path d="{B.DROP}" fill="#fff"/><circle cx="16" cy="17.1" r="2.4" fill="{B.SKY}"/></g>'
              f'<g transform="translate(500 520) scale({s * 0.9:.4f}) translate(-16 -16)"><path d="{B.SPARK}" fill="{B.LIGHT}"/></g>')
    path = write("vk-avatar", avatar, 1000, 1000, pad_ratio=0)
    manifest.append({"svg": path, "png": [{"file": os.path.join(PNG, "vk-avatar_1000.png"), "width": 1000},
                                          {"file": os.path.join(PNG, "vk-avatar_400.png"), "width": 400}]})

    mpath = os.path.join(ROOT, "render-manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    subprocess.run(["node", os.path.join(os.path.dirname(__file__), "render.js"), mpath], check=True)
    os.remove(mpath)
    print(f"{len(manifest)} логотипов → {ROOT}")


if __name__ == "__main__":
    build()
