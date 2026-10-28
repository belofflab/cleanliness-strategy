"""Оформление сообщества VK: обложки, карточки услуг, шаблоны постов и историй (PNG).

    python3 marketing/tools/build_vk.py
Цены «от» — тарифы Тюмени из services/api/app/seed.py (студия, 1 санузел).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import brandkit as B  # noqa: E402

TOOLS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(TOOLS, "..", "vk", "design"))
FONTS = os.path.abspath(os.path.join(TOOLS, "..", "fonts"))

FONT_CSS = "".join(
    f'@font-face{{font-family:Manrope;font-weight:{w};src:url(file://{FONTS}/manrope-{s}-{w}-normal.woff2) format("woff2");'
    f'unicode-range:{r}}}'
    for w in (500, 700, 800) for s, r in (("cyrillic", "U+0400-04FF"), ("latin", "U+0000-03FF,U+2000-22FF")))

BASE_CSS = FONT_CSS + """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Manrope,sans-serif;overflow:hidden}
.navy{background:radial-gradient(1200px 900px at 15% 0%,#0EA5E9 0%,transparent 60%),radial-gradient(900px 700px at 100% 100%,#0369A1 0%,transparent 60%),#0B2A4A;color:#fff}
.light{background:radial-gradient(1000px 800px at 0% 0%,#BAE6FD 0%,transparent 60%),#F4F8FB;color:#0F172A}
.sky{background:linear-gradient(135deg,#0EA5E9,#0369A1);color:#fff}
.kicker{font-weight:700;letter-spacing:.12em;text-transform:uppercase;opacity:.8}
h1,h2{font-weight:800;letter-spacing:-.02em;line-height:1.05}
em{font-style:normal;color:#38BDF8}
.light em{color:#0369A1}
.chip{display:inline-block;font-weight:700;border-radius:999px;border:2px solid rgba(255,255,255,.25);background:rgba(255,255,255,.08)}
.light .chip{border-color:#DDE6EF;background:#fff}
.pill{display:inline-block;font-weight:800;border-radius:999px;background:#0EA5E9;color:#fff}
.light .pill{background:#0369A1}
.ph{font-weight:500;opacity:.65}
"""


def logo(scheme="color-dark", kind="horizontal", width=None, descriptor=None, gid="g"):
    body, w, h = (B.horizontal if kind == "horizontal" else B.stacked)(scheme, descriptor=descriptor, gid=gid)
    svg = B.svg_doc(body, w, h)
    if width:
        svg = svg.replace("<svg ", f'<svg style="width:{width}px;height:auto;display:block" ', 1)
    return svg


def mark_big(size, gid="mb"):
    svg = B.svg_doc(B.mark(0, 0, 32, "color", gid=gid), 32, 32)
    return svg.replace("<svg ", f'<svg style="width:{size}px;height:{size}px;display:block" ', 1)


ASSETS = []


def asset(name, w, h, theme, body, css=""):
    ASSETS.append((name, w, h, f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>{BASE_CSS}{css}'
                               f'body{{width:{w}px;height:{h}px}}</style></head><body class="{theme}">{body}</body></html>'))


# 1. Обложка сообщества (десктоп). Ключевое — в центральной зоне: края обрезаются в мобильном приложении.
asset("cover-desktop_1920x768", 1920, 768, "navy", f"""
<div style="position:absolute;left:360px;right:360px;top:120px;bottom:120px;display:flex;flex-direction:column;justify-content:center;gap:34px">
  {logo(width=520, gid="c1")}
  <h1 style="font-size:64px">Уборка квартир в Тюмени<br><em>с фиксированной ценой</em></h1>
  <div style="display:flex;gap:16px;flex-wrap:wrap">
    <span class="chip" style="font-size:26px;padding:12px 22px">Цена до выезда</span>
    <span class="chip" style="font-size:26px;padding:12px 22px">Оплата после приёмки</span>
    <span class="chip" style="font-size:26px;padding:12px 22px">Переуберём за 24 ч</span>
  </div>
</div>
<div style="position:absolute;right:120px;top:154px;opacity:.95;transform:rotate(8deg)">{mark_big(300, "c1m")}</div>
""")

# 2. Живая обложка для мобильного приложения (кадр 1080×1920)
asset("cover-mobile_1080x1920", 1080, 1920, "navy", f"""
<div style="position:absolute;left:90px;right:90px;top:300px;bottom:520px;display:flex;flex-direction:column;justify-content:center;gap:48px">
  {logo(kind="stacked", width=520, descriptor="клининговая служба", gid="c2")}
  <h1 style="font-size:92px">Чистая квартира<br><em>без сюрпризов</em></h1>
  <div style="display:grid;gap:18px;font-size:44px;font-weight:700">
    <div>Поддерживающая — от 2 400 ₽</div><div>Генеральная — от 4 900 ₽</div><div>После ремонта — от 6 200 ₽</div>
  </div>
  <span class="pill" style="font-size:40px;padding:22px 40px;align-self:flex-start">Расчёт за 7 минут</span>
</div>
""")

# 3. Карточки услуг (раздел «Услуги»)
SERVICES = [
    ("service-maintenance", "Поддерживающая уборка", "от 2 400 ₽", "Полы, пыль, кухня, санузел. Свой клинер по подписке", "light"),
    ("service-general", "Генеральная уборка", "от 4 900 ₽", "Налёт, жир, труднодоступные места. Фотоотчёт", "navy"),
    ("service-post-renovation", "Уборка после ремонта", "от 6 200 ₽", "Строительная пыль, затирка, окна от плёнки", "sky"),
    ("service-windows", "Мытьё окон", "350 ₽ / створка", "Без разводов, вместе с уборкой — без доплаты за выезд", "light"),
    ("service-upholstery", "Химчистка мебели", "1 500 ₽ / предмет", "Диваны, кресла, матрасы на дому", "navy"),
    ("service-office", "Уборка офисов", "по договору", "Ежедневно или по графику, ЭДО и закрывающие документы", "sky"),
]
for i, (name, title, price, text, theme) in enumerate(SERVICES):
    scheme = "color" if theme == "light" else ("1c-white" if theme == "sky" else "color-dark")
    asset(f"{name}_1000x1000", 1000, 1000, theme, f"""
<div style="position:absolute;inset:80px;display:flex;flex-direction:column;justify-content:space-between">
  {logo(scheme, width=360, gid=f"s{i}")}
  <div style="display:grid;gap:26px">
    <h2 style="font-size:78px">{title}</h2>
    <div style="font-size:34px;font-weight:500;opacity:.85;max-width:760px;line-height:1.35">{text}</div>
    <span class="pill" style="font-size:44px;padding:18px 34px;justify-self:start">{price}</span>
  </div>
</div>""")

# 4. Шаблоны постов 1080×1350. Текст в [скобках] — заменить на реальный.
asset("post-template-price_1080x1350", 1080, 1350, "navy", f"""
<div style="position:absolute;inset:90px;display:flex;flex-direction:column;justify-content:space-between">
  {logo(width=420, gid="p1")}
  <div style="display:grid;gap:30px"><div class="kicker" style="font-size:28px">Тюмень · цены 2026</div>
  <h1 style="font-size:84px">Уборка после ремонта<br><em>без «от» и сюрпризов</em></h1>
  <div style="display:grid;gap:14px;font-size:42px;font-weight:700"><div>Студия — 6 200 ₽</div><div>1-комнатная — 9 950 ₽</div>
  <div>2-комнатная — 13 700 ₽</div><div>3-комнатная, 2 с/у — 18 950 ₽</div></div></div>
  <span class="pill" style="font-size:36px;padding:18px 32px;align-self:flex-start">Рассчитать свою — в сообщения</span>
</div>""")
asset("post-template-tip_1080x1350", 1080, 1350, "light", f"""
<div style="position:absolute;inset:90px;display:flex;flex-direction:column;justify-content:space-between">
  {logo("color", width=420, gid="p2")}
  <div style="display:grid;gap:30px"><div class="kicker" style="font-size:28px">Лайфхак клинера</div>
  <h1 style="font-size:84px">[Заголовок совета:<br><em>одна мысль</em>]</h1>
  <div style="display:grid;gap:18px;font-size:40px;font-weight:700"><div>1. [Шаг первый]</div><div>2. [Шаг второй]</div><div>3. [Шаг третий]</div></div></div>
  <div class="ph" style="font-size:30px">Сохраните, чтобы не потерять</div>
</div>""")
asset("post-template-review_1080x1350", 1080, 1350, "light", f"""
<div style="position:absolute;inset:90px;display:flex;flex-direction:column;justify-content:space-between">
  {logo("color", width=420, gid="p3")}
  <div style="display:grid;gap:36px"><div style="font-size:200px;line-height:.6;color:#0EA5E9;font-weight:800">“</div>
  <h1 style="font-size:58px;font-weight:700;line-height:1.25">[Цитата из реального отзыва клиента — с его согласия]</h1>
  <div style="font-size:34px;font-weight:700">[Имя], [ЖК или район] · <span style="color:#0369A1">★★★★★</span> [площадка]</div></div>
  <div class="ph" style="font-size:30px">Только настоящие отзывы — ссылка на оригинал в тексте поста</div>
</div>""")
asset("post-template-promo_1080x1350", 1080, 1350, "sky", f"""
<div style="position:absolute;inset:90px;display:flex;flex-direction:column;justify-content:space-between">
  {logo("1c-white", width=420, gid="p4")}
  <div style="display:grid;gap:30px"><div class="kicker" style="font-size:28px">Групповая скидка ЖК</div>
  <h1 style="font-size:96px">3 квартиры в один день — <span style="color:#0B2A4A">−10%</span></h1>
  <div style="font-size:42px;font-weight:700">5 квартир и больше — −15%</div></div>
  <div style="font-size:32px;font-weight:500;opacity:.9">Перешлите пост в чат своего дома</div>
</div>""")

# 5. История: свободные окна на завтра
asset("story-template-slots_1080x1920", 1080, 1920, "navy", f"""
<div style="position:absolute;left:90px;right:90px;top:280px;bottom:480px;display:flex;flex-direction:column;justify-content:center;gap:40px">
  {logo(width=460, gid="st")}
  <div class="kicker" style="font-size:32px">Свободно на завтра</div>
  <h1 style="font-size:96px">Есть окна<br><em>на уборку</em></h1>
  <div style="display:flex;gap:20px;flex-wrap:wrap">
    <span class="chip" style="font-size:52px;padding:20px 36px">[10:00]</span><span class="chip" style="font-size:52px;padding:20px 36px">[14:00]</span>
  </div>
  <span class="pill" style="font-size:42px;padding:22px 40px;align-self:flex-start">Написать в сообщения</span>
</div>""")


def build():
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "_html")
    os.makedirs(tmp, exist_ok=True)
    jobs = []
    for name, w, h, page in ASSETS:
        path = os.path.join(tmp, f"{name}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(page)
        jobs.append({"html": path, "png": os.path.join(OUT, f"{name}.png"), "w": w, "h": h})
    job_file = os.path.join(tmp, "jobs.json")
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f)
    subprocess.run(["node", "-e", """
const fs=require('fs');const {chromium}=require('playwright');
(async()=>{const jobs=JSON.parse(fs.readFileSync(process.argv[1]));const b=await chromium.launch();
for(const j of jobs){const p=await b.newPage({viewport:{width:j.w,height:j.h}});await p.goto('file://'+j.html);
await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:j.png});await p.close();}await b.close();})()
.catch(e=>{console.error(e);process.exit(1)});""", job_file], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    print(f"{len(ASSETS)} макетов → {OUT}")


if __name__ == "__main__":
    build()
