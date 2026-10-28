"""Техзадание на нанесение для типографии: схемы размещения в масштабе + таблица файлов (A4, PDF).

    python3 marketing/tools/build_techsheet.py      (после build_apparel.py)
"""

from __future__ import annotations

import json
import os
import subprocess

TOOLS = os.path.dirname(os.path.abspath(__file__))
APPAREL = os.path.abspath(os.path.join(TOOLS, "..", "apparel"))

TEE_FRONT = "M300 20 Q380 110 460 20 L560 30 L760 170 L700 270 L640 240 L640 720 L120 720 L120 240 L60 270 L0 170 L200 30 Z"
TEE_BACK = "M300 20 Q380 50 460 20 L560 30 L760 170 L700 270 L640 240 L640 720 L120 720 L120 240 L60 270 L0 170 L200 30 Z"
POLO = TEE_FRONT + " M380 66 V190"
APRON = "M250 0 H510 V40 Q510 120 600 140 V760 H160 V140 Q250 120 250 40 Z"
CAP = "M40 260 Q40 40 230 30 Q420 40 420 260 Z M20 260 H440 Q470 300 380 320 H80 Q-10 300 20 260 Z"


def files():
    with open(os.path.join(APPAREL, "files.json"), encoding="utf-8") as f:
        return {x["file"].rsplit("_", 1)[0]: x for x in json.load(f)}


def garment(view_w, view_h, outline, fill, placements, caption, note):
    """Схема изделия в мм: силуэт + принт в точном размере + размерные подписи."""
    imgs = []
    for p in placements:
        imgs.append(f'<image href="preview/{p["file"]}.png" x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}"/>'
                    f'<rect x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}" fill="none" stroke="#E11D48" stroke-width="2" stroke-dasharray="8 6"/>'
                    f'<text x="{p["x"] + p["w"] / 2}" y="{p["y"] + p["h"] + 26}" text-anchor="middle" class="dim">{p["w"]:.0f} × {p["h"]:.0f} мм</text>'
                    + (f'<text x="{p["x"] + p["w"] / 2}" y="{p["y"] - 10}" text-anchor="middle" class="dim">{p["label"]}</text>' if p.get("label") else ""))
    return (f'<figure><svg viewBox="-20 -40 {view_w + 40} {view_h + 80}">'
            f'<path d="{outline}" fill="{fill}" stroke="#94A3B8" stroke-width="3"/>{"".join(imgs)}</svg>'
            f'<figcaption><b>{caption}</b><span>{note}</span></figcaption></figure>')


def build():
    F = files()

    def p(key, x, y, label=""):
        f = F[key]
        return {"file": f["file"], "x": x, "y": y, "w": f["width_mm"], "h": f["height_mm"], "label": label}

    chest = F["tshirt-chest_white_dark"]
    back = F["tshirt-back_white_dark"]
    page1 = "".join([
        garment(760, 720, TEE_FRONT, "#0B2A4A",
                [p("tshirt-chest_white_dark", 480 - chest["width_mm"] / 2, 130, "100 мм ниже плечевого шва")],
                "Футболка / свитшот — перед",
                "Грудь слева (у носящего). Центр принта — 90–100 мм от середины изделия, верх — 80–100 мм от плечевого шва."),
        garment(760, 720, TEE_BACK, "#0B2A4A",
                [p("tshirt-back_white_dark", 380 - back["width_mm"] / 2, 100, "80 мм от воротника")],
                "Футболка / худи / куртка — спина",
                "По центру, верх — 70–80 мм от воротника. QR ведёт на tyumen.cleanliness.pro с UTM «uniform»."),
    ])
    polo = F["polo-embroidery_white_dark"]
    cap = F["cap-front_white_dark"]
    apron = F["apron-chest_white_dark"]
    page2 = "".join([
        garment(760, 720, POLO, "#0B2A4A", [p("polo-embroidery_white_dark", 490 - polo["width_mm"] / 2, 140)],
                "Поло — вышивка", "Грудь слева, 80 мм, белая нить. Шелкографию на пике не делать — вышивка."),
        garment(460, 320, CAP, "#0B2A4A", [p("cap-front_white_dark", 230 - cap["width_mm"] / 2, 120)],
                "Кепка — перед", "Знак 50 мм по центру передней панели, вышивка белым."),
        garment(760, 760, APRON, "#0B2A4A", [p("apron-chest_white_dark", 380 - apron["width_mm"] / 2, 170)],
                "Фартук — грудь", "Вертикальный логотип 170 мм, верх — 170 мм от верхнего края."),
    ])

    rows = "".join(f'<tr><td><code>{x["file"]}</code></td><td>{x["width_mm"]} × {x["height_mm"]}</td><td>{x["purpose"]}</td></tr>'
                   for x in json.load(open(os.path.join(APPAREL, "files.json"), encoding="utf-8")))
    html = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 0 }}
* {{ box-sizing: border-box }}
body {{ margin: 0; font-family: Inter, "DejaVu Sans", sans-serif; color: #0F172A; font-size: 10.5px }}
.page {{ width: 297mm; height: 210mm; padding: 10mm 12mm; page-break-after: always; display: grid; grid-template-rows: auto 1fr auto; gap: 6mm }}
h1 {{ margin: 0; font-size: 18px }} h1 span {{ color: #0369A1 }}
.sub {{ color: #5F6B7A; margin-top: 2px }}
.figs {{ display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 8mm; align-items: end }}
figure {{ margin: 0; display: grid; gap: 3mm }}
svg {{ width: 100%; height: auto; max-height: 120mm }}
.dim {{ font: 600 22px Inter, sans-serif; fill: #E11D48 }}
figcaption {{ display: grid; gap: 1mm }} figcaption span {{ color: #44546A }}
table {{ border-collapse: collapse; width: 100% }} td, th {{ border-bottom: 1px solid #DDE6EF; padding: 2.2mm 2mm; text-align: left; vertical-align: top }}
th {{ font-size: 9px; text-transform: uppercase; letter-spacing: .06em; color: #6B7A8F }}
code {{ font-size: 9.5px }}
.foot {{ color: #5F6B7A; display: flex; justify-content: space-between }}
.specs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8mm }}
.specs ul {{ margin: 0; padding-left: 4mm; display: grid; gap: 1mm }}
.sw {{ display: inline-block; width: 9px; height: 9px; border-radius: 2px; vertical-align: -1px; margin-right: 4px; border: 1px solid #0002 }}
</style></head><body>
<section class="page"><div><h1>Техзадание на нанесение · <span>Точка Чистоты</span></h1>
<div class="sub">Лист 1 из 3 · Футболки, свитшоты, худи. Масштаб схем условный, размеры принтов — в мм 1:1 в файлах. Красная рамка — граница принта.</div></div>
<div class="figs">{page1}</div>
<div class="foot"><span>Файлы: marketing/apparel/pdf (вектор, текст в кривых) · превью: marketing/apparel/preview</span><span>Цвет ткани на схемах — тёмно-синий (navy)</span></div></section>
<section class="page"><div><h1>Техзадание на нанесение · <span>Точка Чистоты</span></h1>
<div class="sub">Лист 2 из 3 · Поло, кепка, фартук</div></div>
<div class="figs">{page2}</div>
<div class="foot"><span>Вышивку оцифровывает типография по PDF-файлу (формат DST/EMB)</span><span>Пробный образец перед тиражом обязателен</span></div></section>
<section class="page"><div><h1>Техзадание на нанесение · <span>Точка Чистоты</span></h1>
<div class="sub">Лист 3 из 3 · Файлы, цвета, способы нанесения</div></div>
<div class="specs"><div><table><thead><tr><th>Файл</th><th>Размер, мм</th><th>Назначение</th></tr></thead><tbody>{rows}</tbody></table></div>
<div><h3>Цвета</h3><ul>
<li><span class="sw" style="background:#FFFFFF"></span>Белый — все одноцветные принты на тёмной ткани</li>
<li><span class="sw" style="background:#0369A1"></span>Глубокий синий #0369A1 ≈ Pantone 3015 C — одноцветные принты и нить на светлой ткани</li>
<li><span class="sw" style="background:#0EA5E9"></span>Небесный #0EA5E9 ≈ Pantone 2995 C — только в полноцветных (DTF) файлах</li>
<li><span class="sw" style="background:#0F172A"></span>Чернильный #0F172A ≈ Pantone Black 6 C</li>
<li><span class="sw" style="background:#0B2A4A"></span>Ткань: тёмно-синяя (navy) — основная; белая — для светлых вариантов</li></ul>
<h3>Способы</h3><ul>
<li><b>DTF / цифровая печать</b> — файлы <code>_color_light</code>: градиент знака сохраняется.</li>
<li><b>Шелкография</b> — только файлы <code>_white_dark</code> и <code>1c</code>: один цвет, одна сетка.</li>
<li><b>Вышивка</b> — <code>polo-embroidery</code>, <code>cap-front</code>: без градиента; минимум 70 мм для логотипа и 25 мм для знака.</li>
<li><b>QR на спине</b> — печатать без масштабирования ниже 80 мм по стороне QR; на тёмной ткани белая плашка обязательна (модули — вырез).</li>
<li>Перед тиражом — пробный образец и сверка цвета по веерку Pantone.</li></ul></div></div>
<div class="foot"><span>Исходники и пересборка: marketing/tools/build_apparel.py, build_techsheet.py</span><span>Контакт для вопросов типографии — менеджер «Точки Чистоты»</span></div></section>
</body></html>"""
    path = os.path.join(APPAREL, "techsheet.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    subprocess.run(["node", os.path.join(TOOLS, "html2pdf.js"), path, os.path.join(APPAREL, "techsheet.pdf")], check=True)
    os.remove(path)
    print("Техзадание → marketing/apparel/techsheet.pdf")


if __name__ == "__main__":
    build()
