"""Концепция формы: технические эскизы комплекта с нанесением, палитра, знаки статуса (A4, PDF и PNG).

    python3 marketing/tools/build_uniform.py      (после build_apparel.py)
Результат: marketing/apparel/lookbook.pdf и lookbook.png. Описание комплекта — marketing/apparel/uniform-concept.md.
"""

from __future__ import annotations

import json
import os
import subprocess

TOOLS = os.path.dirname(os.path.abspath(__file__))
APPAREL = os.path.abspath(os.path.join(TOOLS, "..", "apparel"))
FONTS = os.path.abspath(os.path.join(TOOLS, "..", "fonts"))

NAVY, NAVY2, SKY, GRAPHITE, SILVER = "#0B2A4A", "#1E3A5F", "#0EA5E9", "#2A3444", "#C3CBD5"
SEAM = f'stroke="{NAVY2}" stroke-width="2" fill="none" stroke-dasharray="5 4"'


def prev(key):
    """Превью печатного файла по префиксу имени (marketing/apparel/preview)."""
    for f in json.load(open(os.path.join(APPAREL, "files.json"), encoding="utf-8")):
        if f["file"].startswith(key):
            return f"file://{APPAREL}/preview/{f['file']}.png"
    raise KeyError(key)


def img(key, x, y, w):
    return f'<image href="{prev(key)}" x="{x}" y="{y}" width="{w}" preserveAspectRatio="xMidYMin meet"/>'


def flat(w, h, body, top=0):
    return f'<svg viewBox="-10 {top - 10} {w + 20} {h - top + 20}" class="flat">{body}</svg>'


TEE = ("M110 14 Q150 40 190 14 L236 26 L300 104 L262 134 L240 118 Q250 230 242 340 Q150 352 58 340 "
       "Q50 230 60 118 L38 134 L0 104 L64 26 Z")
TEE_BACK = ("M110 14 Q150 26 190 14 L236 26 L300 104 L262 134 L240 118 Q250 236 242 352 Q150 366 58 352 "
            "Q50 236 60 118 L38 134 L0 104 L64 26 Z")

tee_front = flat(300, 360, f'<path d="{TEE}" fill="{NAVY}"/>'
                 f'<path d="M118 18 L62 118 M182 18 L238 118" {SEAM}/>'
                 f'<path d="M110 14 Q150 40 190 14" stroke="{SKY}" stroke-width="5" fill="none"/>'
                 + img("tshirt-chest_white_dark", 168, 82, 52) + img("name-patch-sample", 74, 82, 56))
tee_back = flat(300, 370, f'<path d="{TEE_BACK}" fill="{NAVY}"/>'
                f'<path d="M118 18 L62 118 M182 18 L238 118" {SEAM}/>'
                + img("back-slogan-dust", 80, 60, 140)
                + '<path d="M250 300 V350" stroke="#E11D48" stroke-width="2"/><path d="M244 300 H256 M244 350 H256" stroke="#E11D48" stroke-width="2"/>'
                + '<text x="262" y="330" class="ann">+4 см</text>')
hoodie = flat(300, 360, f'<path d="M100 40 Q96 -10 150 -16 Q204 -10 200 40 Q150 70 100 40 Z" fill="{NAVY2}"/>'
              f'<path d="M100 40 Q150 64 200 40 L250 52 L300 300 L268 312 L238 150 L240 360 L60 360 L62 150 L32 312 L0 300 L50 52 Z" fill="{NAVY}"/>'
              f'<path d="M150 50 V360" stroke="{SKY}" stroke-width="3"/>'
              f'<path d="M72 270 Q104 256 142 262 V330 H72 Z M228 270 Q196 256 158 262 V330 H228 Z" fill="none" stroke="{NAVY2}" stroke-width="2"/>'
              f'<rect x="60" y="344" width="180" height="16" fill="{NAVY2}"/>'
              f'<path d="M100 40 L50 52 M200 40 L250 52 M0 300 L32 312 M300 300 L268 312" stroke="{SILVER}" stroke-width="6" stroke-linecap="round"/>'
              + img("tshirt-chest_white_dark", 168, 96, 52), top=-20)
apron = flat(300, 370, f'<path d="M100 2 Q80 -26 56 -36 M200 2 Q220 -26 244 -36" stroke="{SKY}" stroke-width="7" fill="none" stroke-linecap="round"/>'
             f'<path d="M52 92 L8 110 M248 92 L292 110" stroke="{SKY}" stroke-width="7" stroke-linecap="round"/>'
             f'<path d="M95 0 H205 V22 Q205 70 250 82 V350 Q250 360 240 360 H60 Q50 360 50 350 V82 Q95 70 95 22 Z" fill="{NAVY}"/>'
             f'<rect x="164" y="26" width="32" height="50" rx="4" fill="none" stroke="{SKY}" stroke-width="2.5"/>'
             f'<rect x="68" y="236" width="78" height="72" rx="6" fill="none" stroke="{SKY}" stroke-width="2.5"/>'
             f'<rect x="154" y="236" width="78" height="72" rx="6" fill="none" stroke="{SKY}" stroke-width="2.5"/>'
             f'<rect x="246" y="150" width="14" height="30" rx="5" fill="none" stroke="{SKY}" stroke-width="3"/>'
             + img("apron-chest_white_dark", 104, 96, 92), top=-40)
pants = flat(300, 360, f'<path d="M58 0 H242 L262 180 L246 352 H166 L152 150 L148 150 L134 352 H54 L38 180 Z" fill="{GRAPHITE}"/>'
             f'<rect x="58" y="0" width="184" height="22" fill="#1C2533"/>'
             f'<path d="M140 22 Q136 46 128 56 M160 22 Q164 46 172 56" stroke="{SKY}" stroke-width="2.5" fill="none"/>'
             f'<path d="M64 30 Q84 60 74 96 M236 30 Q216 60 226 96" stroke="#1C2533" stroke-width="2.5" fill="none"/>'
             f'<rect x="58" y="196" width="66" height="64" rx="8" fill="#323E50" stroke="#1C2533" stroke-width="2"/>'
             f'<rect x="176" y="196" width="66" height="64" rx="8" fill="#323E50" stroke="#1C2533" stroke-width="2"/>'
             f'<path d="M64 202 H118 M182 202 H236" {SEAM}/>'
             f'<rect x="54" y="336" width="80" height="16" fill="#1C2533"/><rect x="166" y="336" width="80" height="16" fill="#1C2533"/>'
             + img("sleeve_white_dark", 206, 96, 24))
cap = flat(300, 220, f'<path d="M62 160 Q58 52 150 44 Q242 52 238 160 Z" fill="{NAVY}"/>'
                     f'<path d="M150 52 V160 M110 62 Q98 104 102 160 M190 62 Q202 104 198 160" {SEAM}/>'
                     f'<circle cx="150" cy="46" r="6" fill="{NAVY2}"/>'
                     f'<path d="M44 160 Q150 140 256 160 Q258 190 150 204 Q42 190 44 160 Z" fill="{NAVY2}"/>'
           + img("cap-front_white_dark", 130, 88, 40))
gloves = flat(300, 220, "".join(
    f'<g transform="translate({dx},{dy}) rotate({r} 60 110)">'
    f'<rect x="20" y="70" width="80" height="110" rx="26" fill="{SKY}"/>'
    + "".join(f'<rect x="{x}" y="{y}" width="18" height="70" rx="9" fill="{SKY}"/>' for x, y in ((22, 22), (42, 10), (62, 14), (82, 30)))
    + f'<rect x="-6" y="96" width="18" height="56" rx="9" fill="{SKY}" transform="rotate(-38 3 124)"/>'
    f'<rect x="24" y="150" width="72" height="34" rx="10" fill="#38BDF8"/></g>' for dx, dy, r in ((40, 10, -8), (150, 20, 10))))
shoebag = flat(300, 240, f'<path d="M70 30 H230 L240 230 Q240 240 230 240 H70 Q60 240 60 230 Z" fill="{NAVY}"/>'
                         f'<path d="M70 30 Q150 50 230 30" stroke="{SKY}" stroke-width="4" fill="none"/>'
                         f'<path d="M110 36 Q100 -10 150 -14 Q200 -10 190 36" stroke="{SKY}" stroke-width="4" fill="none"/>'
              + img("apron-chest_white_dark", 100, 90, 100), top=-20)

ITEMS = [
    (tee_front, "Футболка — перед", "CVC 60/40, 190 г/м², реглан, женский и мужской крой. Логотип слева, имя справа на липучке"),
    (tee_back, "Футболка — спина", "Спинка длиннее на 4 см — не оголяется при наклоне. Слоган: 1 из 4"),
    (hoodie, "Худи на молнии", "Футер 300 г/м². Снимается, не задевая причёску. Светоотражающий кант"),
    (apron, "Фартук", "Водоотталкивающий, H-лямки без нагрузки на шею. Карманы: тряпки, телефон, петля под распылитель"),
    (pants, "Брюки-джоггеры", "Стрейч-твил 240 г/м², графит. Карманы под наколенники, манжеты не цепляются"),
    (cap, "Кепка", "Для окон, балконов и дороги. В квартире — без кепки, волосы собраны"),
    (gloves, "Перчатки", "Нитрил небесного цвета — продолжение палитры, видны в кадре фотоотчёта"),
    (shoebag, "Мешок для сменной обуви", "Переобуваемся у порога: заметнее и бережнее к полу, чем бахилы"),
]

SWATCHES = [(NAVY, "Тёмно-синий", "основа: футболки, худи, фартук"), (GRAPHITE, "Графит", "брюки: не видно следов на коленях"),
            (SKY, "Небесный", "акценты: кант, лямки, перчатки"), ("#FFFFFF", "Белый", "надписи и логотип"),
            (SILVER, "Серебро", "светоотражающие элементы")]


def page():
    cards = "".join(f'<div class="card">{svg}<b>{t}</b><span>{d}</span></div>' for svg, t, d in ITEMS)
    sw = "".join(f'<div class="sw"><i style="background:{c}"></i><div><b>{n}</b><span>{d}</span></div></div>' for c, n, d in SWATCHES)
    status = "".join(f'<img src="{prev(k)}" style="height:{h}px">' for k, h in
                     (("chevron-certified", 34), ("chevron-senior", 34), ("chevron-lead", 34), ("name-patch", 22), ("badge-template", 52)))
    fonts = "".join(f'@font-face{{font-family:Manrope;font-weight:{w};src:url(file://{FONTS}/manrope-{s}-{w}-normal.woff2)}}'
                    for w in (500, 700, 800) for s in ("cyrillic", "latin"))
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>{fonts}
@page {{ size: A4 landscape; margin: 0 }}
* {{ box-sizing: border-box; margin: 0 }}
body {{ width: 1123px; height: 794px; padding: 30px 36px; font-family: Manrope, sans-serif; color: #0F172A; background: #F6F9FC;
       display: grid; grid-template-rows: auto 1fr auto; gap: 16px }}
h1 {{ font-size: 24px; font-weight: 800 }} h1 span {{ color: #0369A1 }}
.sub {{ font-size: 13px; color: #44546A; margin-top: 4px; font-weight: 500 }}
.grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; min-height: 0 }}
.card {{ background: #fff; border: 1px solid #DDE6EF; border-radius: 14px; padding: 10px 12px; display: grid; grid-template-rows: 1fr auto auto; gap: 3px }}
.flat {{ width: 100%; height: 170px; min-width: 0 }}
.ann {{ font: 700 15px Manrope; fill: #E11D48 }}
.card b {{ font-size: 13px; font-weight: 800 }} .card span {{ font-size: 10.5px; color: #44546A; line-height: 1.3; font-weight: 500 }}
.foot {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); gap: 16px; align-items: center }}
.sws {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px 10px }}
.sw {{ display: flex; gap: 7px; align-items: flex-start; font-size: 10px }} .sw i {{ flex: none; width: 22px; height: 22px; border-radius: 6px; border: 1px solid #0002 }}
.sw b {{ display: block; font-size: 11px }} .sw span {{ color: #44546A }}
.status {{ display: flex; gap: 7px; align-items: center; justify-content: flex-start; overflow: hidden; background: {NAVY}; border-radius: 12px; padding: 10px 12px }}
.status em {{ font-style: normal; color: #B6C3D3; font-size: 10.5px; font-weight: 700; margin-right: 4px; width: 84px; flex: none }}
</style></head><body>
<div><h1>Форма «Точки Чистоты» · <span>концепция комплекта</span></h1>
<div class="sub">Образ сервисного техника, а не «уборщицы»: приталенный крой, тёмно-синий с небесными акцентами, крупные белые надписи.<br>Печатные файлы — marketing/apparel/pdf, размещение и размеры — techsheet.pdf, описание — uniform-concept.md</div></div>
<div class="grid">{cards}</div>
<div class="foot"><div class="sws">{sw}</div><div class="status"><em>Знаки статуса и доверия: грейд, имя, бейдж</em>{status}</div></div>
</body></html>"""


def build():
    html = os.path.join(APPAREL, "lookbook.html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(page())
    subprocess.run(["node", os.path.join(TOOLS, "html2pdf.js"), html, os.path.join(APPAREL, "lookbook.pdf")], check=True)
    subprocess.run(["node", "-e", """
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1123,height:794},deviceScaleFactor:2});await p.goto('file://'+process.argv[1]);
await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:process.argv[2]});await b.close();})()
.catch(e=>{console.error(e);process.exit(1)});""", html, os.path.join(APPAREL, "lookbook.png")], check=True)
    os.remove(html)
    print("Концепция формы → marketing/apparel/lookbook.pdf, lookbook.png")


if __name__ == "__main__":
    build()
