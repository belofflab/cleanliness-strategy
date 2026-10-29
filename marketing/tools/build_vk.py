"""Оформление сообществ VK «Точки Чистоты»: обложка, живая обложка, меню, услуги, посты (PNG).

    python3 marketing/tools/build_vk.py          # Тюмень, https://vk.ru/cleanliness_tmn → vk/design
    python3 marketing/tools/build_vk.py ufa      # Уфа, https://vk.ru/cleanliness_ufa → vk/ufa/design
Цены Тюмени — прайс стратегии (студия, 1 санузел), цены Уфы — «от» с сайта ufa.cleanliness.pro
(тарифы services/api/app/seed.py). Иллюстрации — tools/illustrations.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import brandkit as B  # noqa: E402
import illustrations as I  # noqa: E402

TOOLS = os.path.dirname(os.path.abspath(__file__))

CITIES = {
    "tyumen": dict(
        out=("vk", "design"), loc="в Тюмени", kicker="Тюмень · цены 2026", site="tyumen.cleanliness.pro",
        prices=("от 2 400 ₽", "от 4 900 ₽", "от 6 200 ₽"), windows="350 ₽", upholstery="1 500 ₽",
        maintenance_note="Свой клинер по подписке −15%", menu_prices="Студия — от 2 400 ₽",
        live_notes=("2-комн.: поддерживающая — 3 900 ₽, генеральная — 10 600 ₽,<br>после ремонта — 13 700 ₽",
                    "Окна — 350 ₽ за створку · химчистка — 1 500 ₽ за предмет"),
        price_post=("Уборка после ремонта<br><em>без «от» и сюрпризов</em>",
                    ("Студия — 6 200 ₽", "1-комнатная — 9 950 ₽", "2-комнатная — 13 700 ₽", "3-комнатная, 2 с/у — 18 950 ₽")),
        subscription=True, gifts=True, promo=True),
    "ufa": dict(
        out=("vk", "ufa", "design"), loc="в Уфе", kicker="Уфа · цены 2026", site="ufa.cleanliness.pro",
        prices=("от 1 650 ₽", "от 3 750 ₽", "от 5 350 ₽"), windows="380 ₽", upholstery="1 600 ₽",
        maintenance_note="Свои средства и инвентарь", menu_prices="Уборка — от 1 650 ₽",
        live_notes=("Окна — 380 ₽ за створку · химчистка — 1 600 ₽ за предмет",
                    "Офисы — по договору"),
        price_post=("Цены на уборку<br><em>без сюрпризов</em>",
                    ("Поддерживающая — от 1 650 ₽", "Генеральная — от 3 750 ₽", "После ремонта — от 5 350 ₽",
                     "Окна — 380 ₽ за створку")),
        subscription=False, gifts=False, promo=False),
}
CITY_SLUG = sys.argv[1] if len(sys.argv) > 1 else "tyumen"
C = CITIES[CITY_SLUG]
OUT = os.path.abspath(os.path.join(TOOLS, "..", *C["out"]))
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
.fresh{background:radial-gradient(900px 700px at 82% 18%,#CDEEFF 0%,transparent 62%),radial-gradient(900px 700px at 0% 100%,#E0F2FE 0%,transparent 60%),linear-gradient(160deg,#FAFDFF 0%,#EAF6FE 100%);color:#0F172A}
.fresh em{color:#0369A1}
.fresh .chip{border-color:#CFE4F2;background:rgba(255,255,255,.9)}
.fresh .pill{background:#0369A1}
.glow{position:absolute;border-radius:50%;background:radial-gradient(closest-side,rgba(255,255,255,.95),rgba(255,255,255,0))}
.navy .glow,.sky .glow{background:radial-gradient(closest-side,rgba(56,189,248,.45),rgba(56,189,248,0))}
.kicker{font-weight:700;letter-spacing:.12em;text-transform:uppercase;opacity:.8}
h1,h2{font-weight:800;letter-spacing:-.02em;line-height:1.05}
em{font-style:normal;color:#38BDF8}
.light em{color:#0369A1}
.chip{display:inline-block;white-space:nowrap;font-weight:700;border-radius:999px;border:2px solid rgba(255,255,255,.25);background:rgba(255,255,255,.08)}
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


def art(w, h, body, left, top, extra=""):
    return I.svg(w, h, body, f"position:absolute;left:{left}px;top:{top}px;{extra}")


def ck(size=40, color="#0EA5E9"):
    return I.svg(size, size, I.check_badge(size / 2, size / 2, size / 2, color), "flex:none")


def chips(items, size=26, pad="12px 22px"):
    return "".join(f'<span class="chip" style="font-size:{size}px;padding:{pad}">{t}</span>' for t in items)


TRUST = ["Цена до выезда", "Оплата после приёмки", "Переуберём за 24 ч"]

# 1. Обложка сообщества (десктоп и мобильная веб-версия). Текст — в зоне x 300–1620, y 110–660:
#    края и полосы сверху и снизу на части экранов обрезаются, внизу слева — аватар.
COVER_SCENE = ('<ellipse cx="410" cy="566" rx="390" ry="36" fill="#DDF0FC"/>'
               + I.window(232, 34, 250, 292) + I.plant(530, 300, 1.32) + I.bucket(70, 372, 1.4) + I.spray(318, 330, 1.3)
               + I.sponge(430, 500, 1.0) + I.bubble(52, 330, 26) + I.bubble(112, 296, 15) + I.bubble(726, 250, 20)
               + I.bubble(690, 430, 12) + I.sparkle(190, 130, 24, I.SKY) + I.sparkle(660, 96, 16, I.SUN)
               + I.sparkle(130, 520, 11, I.PALE))
asset("cover-desktop_1920x768", 1920, 768, "fresh", f"""
<div class="glow" style="left:1000px;top:-180px;width:960px;height:960px"></div>
{art(820, 700, COVER_SCENE, 1010, 40)}
<div style="position:absolute;left:300px;top:150px;width:760px;display:flex;flex-direction:column;gap:28px">
  {logo("color", width=400, gid="c1")}
  <h1 style="font-size:86px">Уборка квартир<br>{C["loc"]}</h1>
  <div style="font-size:36px;font-weight:700;color:#0369A1;margin-top:-6px">Цена до выезда — на месте не меняется</div>
  <div style="display:flex;gap:14px">{chips(TRUST[1:])}</div>
</div>""")

# 2. Живая обложка для приложения: 5 кадров 1080×1920. Приложение растягивает кадр на высоту экрана, и на свёрнутой
#    странице сообщества видна только полоса x 110–970, y 430–1510: сверху её закрывают статус-бар и кнопки (до y 650),
#    снизу — аватар, название и кнопки (от y 1070). Поэтому главный текст — только в полосе LIVE_SAFE (y 660–1040).
#    Выше y 430 и ниже y 1520 — то, что видно, лишь когда обложку открывают на весь экран: логотип и иллюстрации.
LIVE_SAFE = "position:absolute;left:160px;right:160px;top:660px;height:380px;display:flex;flex-direction:column;" \
            "justify-content:center;align-items:center;gap:24px;text-align:center"
LIVE_TOP = "position:absolute;left:0;right:0;top:200px;display:flex;justify-content:center"
LIVE_BOTTOM = "position:absolute;left:0;right:0;top:1530px;display:flex;justify-content:center;align-items:flex-end;gap:40px"
LIVE_SCENE = ('<ellipse cx="380" cy="560" rx="360" ry="34" fill="#DDF0FC"/>'
              + I.window(210, 20, 240, 280) + I.plant(480, 280, 1.3) + I.bucket(50, 350, 1.4) + I.spray(290, 310, 1.3)
              + I.sponge(400, 486, .95) + I.bubble(40, 320, 24) + I.bubble(96, 290, 14) + I.bubble(700, 220, 18)
              + I.sparkle(170, 110, 22, I.SKY) + I.sparkle(640, 70, 15, I.SUN))
asset("live-cover-1_1080x1920", 1080, 1920, "fresh", f"""
<div class="glow" style="left:90px;top:420px;width:900px;height:900px"></div>
<div style="{LIVE_TOP}">{logo("color", kind="stacked", width=260, descriptor="клининговая служба", gid="l1")}</div>
<div style="{LIVE_SAFE}">
  <h1 style="font-size:88px">Чистая квартира<br><em>без сюрпризов</em></h1>
  <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center">{chips(TRUST[:2], 30, "14px 24px")}</div>
</div>
{art(760, 620, LIVE_SCENE, 160, 1290, "opacity:.9")}
""")

PRICE_ROWS = list(zip(("Поддерживающая", "Генеральная", "После ремонта"), C["prices"]))
rows = "".join(f'<div class="row"><span>{t}</span><b>{p}</b></div>' for t, p in PRICE_ROWS)
asset("live-cover-2_1080x1920", 1080, 1920, "navy", f"""
<div style="{LIVE_TOP}">{logo(width=340, gid="l2")}</div>
<div style="{LIVE_SAFE};gap:22px">
  <h1 style="font-size:72px">Цена известна<br><em>до выезда</em></h1>
  <div style="display:flex;flex-direction:column;gap:8px;width:680px">{rows}</div>
</div>
<div style="{LIVE_BOTTOM};flex-direction:column;align-items:center;gap:18px;text-align:center">
  {"".join(f'<div style="font-size:30px;font-weight:500;opacity:.85">{n}</div>' for n in C["live_notes"])}
</div>""", ".row{display:flex;justify-content:space-between;align-items:baseline;font-size:34px;font-weight:700;"
           "padding:9px 26px;border-radius:24px;background:rgba(255,255,255,.08)}.row b{color:#38BDF8;font-weight:800}")

STEPS = [("Напишите", "цена за 7 минут"), ("Приедем", "в 2-часовое окно"), ("Примите работу", "оплата после")]
steps = "".join(f'<div class="step"><span class="num">{i + 1}</span><span><b>{t}</b> — {d}</span></div>'
                for i, (t, d) in enumerate(STEPS))
asset("live-cover-3_1080x1920", 1080, 1920, "fresh", f"""
<div class="glow" style="left:90px;top:420px;width:900px;height:900px"></div>
<div style="{LIVE_TOP}">{logo("color", width=340, gid="l3")}</div>
<div style="{LIVE_SAFE};gap:22px">
  <h1 style="font-size:72px">Три шага до <em>чистоты</em></h1>
  <div style="display:flex;flex-direction:column;gap:10px;width:720px">{steps}</div>
</div>
<div style="{LIVE_BOTTOM}">{I.svg(170, 180, I.stopwatch(12, 2, 1.05), "flex:none")}{I.svg(170, 180, I.bucket(2, 30, 1.05), "flex:none")}{I.svg(170, 180, I.phone_report(34, 4, .84), "flex:none")}</div>
""", ".step{display:flex;align-items:center;gap:20px;font-size:34px;font-weight:500;color:#334155;text-align:left;"
     "padding:10px 22px;border-radius:24px;background:#fff;border:2px solid #DCEBF6}.step b{color:#0F172A;font-weight:800}"
     ".num{flex:none;width:46px;height:46px;border-radius:50%;background:#0EA5E9;color:#fff;font-weight:800;font-size:28px;"
     "display:flex;align-items:center;justify-content:center}")

asset("live-cover-4_1080x1920", 1080, 1920, "sky", f"""
<div class="glow" style="left:90px;top:420px;width:900px;height:900px;opacity:.35"></div>
<div style="{LIVE_TOP}">{logo("1c-white", width=340, gid="l4")}</div>
<div style="{LIVE_SAFE}">
  <h1 style="font-size:76px">Не понравилось —<br><span style="color:#0B2A4A">переуберём бесплатно</span></h1>
  <div style="font-size:36px;font-weight:700">в течение 24 часов после уборки</div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center">{chips(["Фотоотчёт до и после", "Работаем по чек-листу"], 28, "12px 22px")}</div>
</div>
<div style="{LIVE_BOTTOM}">{I.svg(260, 290, I.shield(25, 12, 1.6) + I.sparkle(20, 240, 12) + I.sparkle(240, 180, 8), "flex:none")}</div>
""")

asset("live-cover-5_1080x1920", 1080, 1920, "navy", f"""
<div style="{LIVE_TOP}">{logo(width=340, gid="l5")}</div>
<div style="{LIVE_SAFE}">
  <h1 style="font-size:92px">Расчёт<br><em>за 7 минут</em></h1>
  <div style="font-size:36px;font-weight:500;line-height:1.35;opacity:.9">Нажмите «Сообщения» и пришлите<br>площадь и тип уборки</div>
</div>
<div style="{LIVE_BOTTOM};flex-direction:column;align-items:center;gap:30px">
  {I.svg(230, 250, I.stopwatch(12, 6, 1.5) + I.sparkle(210, 40, 12, I.SUN), "flex:none")}
  <span class="pill" style="font-size:34px;padding:18px 38px">{C["site"]}</span>
</div>""")

# 3. Меню сообщества: 6 пунктов 752×512 (вдвое больше минимальных 376×256 — чётко на любых экранах)
MENU = [("menu-1-prices", "fresh", "Цены", C["menu_prices"], I.spray(150, 40, 1.15) + I.sponge(20, 190, 1.0) + I.bubble(60, 130, 22)),
        ("menu-2-order", "sky", "Расчёт<br>за 7 минут", "Напишите площадь", I.stopwatch(70, 40, 1.45) + I.sparkle(290, 50, 14)),
        ("menu-3-subscription", "navy", "Подписка<br>−15%", "Свой клинер раз в неделю", I.calendar(50, 60, 1.4) + I.sparkle(280, 50, 14, I.SUN)),
        ("menu-4-guarantee", "fresh", "Гарантия", "Переуберём за 24 часа", I.shield(70, 40, 1.45) + I.sparkle(40, 250, 10, I.SKY)),
        ("menu-5-gift", "sky", "Сертификаты", "На 5, 10 или 15 тысяч", I.gift(150, 0, 1.3)),
        ("menu-6-jobs", "navy", "Работа<br>у нас", f"Ищем клинеров {C['loc']}", I.bucket(20, 130, 1.25) + I.squeegee(150, 70, .95))]
MENU = [m for m in MENU if (m[0] != "menu-3-subscription" or C["subscription"]) and (m[0] != "menu-5-gift" or C["gifts"])]
for name, theme, title, sub, ill in MENU:
    sub_color = "#334155" if theme == "fresh" else "rgba(255,255,255,.85)"
    asset(f"{name}_752x512", 752, 512, theme, f"""
<div class="glow" style="left:340px;top:-40px;width:520px;height:520px;opacity:{.9 if theme == 'fresh' else .18}"></div>
{art(360, 330, ill, 380, 120)}
<div style="position:absolute;left:48px;top:48px;bottom:48px;width:400px;display:flex;flex-direction:column;justify-content:space-between">
  {logo("color" if theme == "fresh" else ("1c-white" if theme == "sky" else "color-dark"), width=230, gid=name)}
  <div><h2 style="font-size:{58 if len(title) > 10 and "<br>" not in title else 66}px">{title}</h2><div style="font-size:28px;font-weight:700;color:{sub_color};margin-top:14px">{sub}</div></div>
</div>""")

# 4. Карточки услуг 1000×1000 (раздел «Услуги» или «Товары»)
SERVICES = [
    ("service-maintenance", "Поддерживающая уборка", C["prices"][0], f"Полы, пыль, кухня, санузел. {C['maintenance_note']}",
     I.spray(330, 40, 1.9) + I.sponge(90, 270, 1.7) + I.bubble(120, 120, 36) + I.bubble(190, 70, 20) + I.sparkle(620, 90, 26, I.SKY)),
    ("service-general", "Генеральная уборка", C["prices"][1], "Налёт, жир, труднодоступные места. Фотоотчёт до и после",
     I.bucket(60, 130, 2.0) + I.spray(420, 40, 1.75) + I.sparkle(620, 70, 28, I.SUN) + I.sparkle(80, 80, 18, I.SKY)),
    ("service-post-renovation", "Уборка после ремонта", C["prices"][2], "Строительная пыль, затирка, окна от плёнки",
     I.roller(70, 40, 1.75, -24) + I.bucket(360, 150, 1.8) + I.sparkle(640, 90, 24, I.SKY)),
    ("service-windows", "Мытьё окон", f"{C['windows']} / створка", "Без разводов. Вместе с уборкой — без доплаты за выезд",
     I.window(170, 10, 320, 360) + I.squeegee(470, 160, 1.6, -24) + I.sparkle(110, 90, 22, I.SKY)),
    ("service-upholstery", "Химчистка мебели", f"{C['upholstery']} / предмет", "Диваны, кресла, матрасы — на дому",
     I.sofa(70, 150, 2.05) + I.spray(560, 30, 1.25) + I.bubble(60, 110, 26)),
    ("service-office", "Уборка офисов", "по договору", "Ежедневно или по графику. Договор, ЭДО, закрывающие документы",
     I.building(150, 0, 1.55) + I.calendar(430, 190, 1.35) + I.sparkle(110, 80, 22, I.SUN)),
]
for i, (name, title, price, text, ill) in enumerate(SERVICES):
    asset(f"{name}_1000x1000", 1000, 1000, "fresh", f"""
<div class="glow" style="left:120px;top:-60px;width:760px;height:760px"></div>
<div style="position:absolute;left:70px;top:62px">{logo("color", width=300, gid=f"s{i}")}</div>
{art(760, 420, ill, 120, 130)}
<div style="position:absolute;left:70px;right:70px;bottom:66px;display:grid;gap:20px">
  <h2 style="font-size:70px">{title}</h2>
  <div style="font-size:32px;font-weight:500;color:#334155;max-width:820px;line-height:1.35">{text}</div>
  <span class="pill" style="font-size:44px;padding:16px 34px;justify-self:start">{price}</span>
</div>""")

# 5. Закреплённый пост 1080×1350
asset("pinned-post_1080x1350", 1080, 1350, "fresh", f"""
<div class="glow" style="left:420px;top:700px;width:760px;height:760px"></div>
{art(420, 360, I.bucket(20, 150, 1.3) + I.spray(230, 70, 1.2) + I.bubble(30, 120, 22) + I.sparkle(390, 60, 18, I.SUN), 600, 780)}
<div style="position:absolute;left:84px;right:84px;top:84px;display:flex;flex-direction:column;gap:30px">
  {logo("color", width=400, gid="pp")}
  <div class="kicker" style="font-size:28px;margin-top:20px;color:#0369A1">Добро пожаловать</div>
  <h1 style="font-size:80px">Уборка {C["loc"]}<br><em>с ценой до выезда</em></h1>
  <div style="display:grid;gap:20px;font-size:36px;font-weight:700;margin-top:8px">
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Расчёт за 7 минут в сообщениях</div>
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Свои средства и инвентарь</div>
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Оплата после приёмки работы</div>
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Не понравилось — переуберём за 24 ч</div>
  </div>
  <div style="display:grid;gap:10px;font-size:32px;font-weight:500;color:#334155;margin-top:14px;max-width:520px">
    {"".join(f'<div>{t} — <b style="color:#0F172A">{p}</b></div>' for t, p in PRICE_ROWS)}</div>
</div>
<span class="pill" style="position:absolute;left:84px;bottom:84px;font-size:36px;padding:20px 36px">Написать — расчёт за 7 минут</span>
""")

# 4. Шаблоны постов 1080×1350. Текст в [скобках] — заменить на реальный.
asset("post-template-price_1080x1350", 1080, 1350, "navy", f"""
<div style="position:absolute;inset:90px;display:flex;flex-direction:column;justify-content:space-between">
  {logo(width=420, gid="p1")}
  <div style="display:grid;gap:30px"><div class="kicker" style="font-size:28px">{C["kicker"]}</div>
  <h1 style="font-size:84px">{C["price_post"][0]}</h1>
  <div style="display:grid;gap:14px;font-size:42px;font-weight:700">{"".join(f"<div>{r}</div>" for r in C["price_post"][1])}</div></div>
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
(asset if C["promo"] else (lambda *_: None))("post-template-promo_1080x1350", 1080, 1350, "sky", f"""
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


# 6. Примерный вид страницы сообщества (нейтральная рамка, не интерфейс VK) — для согласования.
#    Рендерятся последними: вставляют уже готовые PNG.
def img(name, style):
    return f'<img src="file://{OUT}/{name}.png" style="display:block;{style}">'


AVATAR = os.path.abspath(os.path.join(TOOLS, "..", "brand", "png", "vk-avatar_1000.png"))
NAME = f"Точка Чистоты — клининг {C['loc']}"
STATUS = "Цена до выезда · оплата после приёмки · ответ за 7 минут"
UI_CSS = (".ui{background:#EDEEF0;color:#0F172A}.box{background:#fff;border-radius:14px}"
          ".btn{display:inline-block;font-weight:700;border-radius:10px;padding:12px 24px}"
          ".lbl{font-size:15px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:.06em}")
tiles = "".join(img(n + "_752x512", "width:290px;height:197px;border-radius:12px") for n, *_ in MENU[:4])
cards = "".join(img(n + "_1000x1000", "width:190px;height:190px;border-radius:12px") for n, *_ in SERVICES)
asset("preview-desktop", 1600, 1200, "ui", f"""
<div style="position:absolute;left:180px;top:24px;width:1240px">
  {img("cover-desktop_1920x768", "width:1240px;height:496px;border-radius:14px 14px 0 0")}
  <div class="box" style="border-radius:0 0 14px 14px;height:130px;position:relative">
    <img src="file://{AVATAR}" style="position:absolute;left:32px;top:-56px;width:150px;height:150px;border-radius:50%;border:5px solid #fff">
    <div style="position:absolute;left:206px;top:22px"><div style="font-size:28px;font-weight:800">{NAME}</div>
      <div style="font-size:18px;color:#64748B;margin-top:8px">{STATUS}</div></div>
    <div style="position:absolute;right:28px;top:40px;display:flex;gap:12px">
      <span class="btn" style="background:#E8EEF5;font-size:18px">Подписаться</span>
      <span class="btn" style="background:#0369A1;color:#fff;font-size:18px">Написать</span></div>
  </div>
  <div class="box" style="margin-top:18px;padding:22px 24px"><div class="lbl">Меню</div>
    <div style="display:flex;gap:13px;margin-top:16px">{tiles}</div></div>
  <div class="box" style="margin-top:18px;padding:22px 24px"><div class="lbl">Услуги</div>
    <div style="display:flex;gap:12px;margin-top:16px">{cards}</div></div>
</div>""", UI_CSS)

asset("preview-mobile", 1000, 1900, "ui", f"""
<div style="position:absolute;left:110px;top:40px;width:780px;height:1820px;border-radius:64px;background:#fff;overflow:hidden;
  box-shadow:0 30px 80px rgba(15,23,42,.18);border:14px solid #0F172A">
  <div style="height:940px;overflow:hidden;position:relative">{img("live-cover-1_1080x1920", "width:939px;margin:-375px 0 0 -95px")}
    <div style="position:absolute;left:0;right:0;bottom:0;height:240px;background:linear-gradient(rgba(255,255,255,0),#fff)"></div></div>
  <div style="padding:0 36px;position:relative;margin-top:-90px">
    <img src="file://{AVATAR}" style="width:150px;height:150px;border-radius:50%;border:6px solid #fff">
    <div style="font-size:34px;font-weight:800;margin-top:14px;line-height:1.2">{NAME}</div>
    <div style="font-size:22px;color:#64748B;margin-top:10px">{STATUS}</div>
    <div style="display:flex;gap:14px;margin-top:26px">
      <span class="btn" style="flex:1;text-align:center;background:#0369A1;color:#fff;font-size:24px;padding:18px">Написать</span>
      <span class="btn" style="flex:1;text-align:center;background:#E8EEF5;font-size:24px;padding:18px">Подписаться</span></div>
    <div style="display:flex;gap:16px;margin-top:34px;width:1200px">{"".join(img(n + "_752x512", "width:300px;height:204px;border-radius:16px") for n, *_ in MENU[:4])}</div>
    <div class="lbl" style="margin-top:34px;font-size:20px">Услуги</div>
    <div style="display:flex;gap:16px;margin-top:16px;width:1200px">{"".join(img(n + "_1000x1000", "width:220px;height:220px;border-radius:16px") for n, *_ in SERVICES[:4])}</div>
  </div>
</div>""", UI_CSS)


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
