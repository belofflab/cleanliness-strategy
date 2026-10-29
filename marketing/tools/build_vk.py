"""Оформление сообщества VK https://vk.ru/cleanliness_tmn: обложка, живая обложка, меню, услуги, посты (PNG).

    python3 marketing/tools/build_vk.py
Цены «от» — тарифы Тюмени из services/api/app/seed.py (студия, 1 санузел). Иллюстрации — tools/illustrations.py.
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
  <h1 style="font-size:86px">Уборка квартир<br>в Тюмени</h1>
  <div style="font-size:36px;font-weight:700;color:#0369A1;margin-top:-6px">Цена до выезда — на месте не меняется</div>
  <div style="display:flex;gap:14px">{chips(TRUST[1:])}</div>
</div>""")

# 2. Живая обложка для приложения: 5 кадров 1080×1920. Заголовок — в верхней половине (y 220–700): на странице
#    сообщества низ кадра закрывают аватар, название и кнопки; целиком кадр виден, когда обложку открывают.
LIVE_SCENE = ('<ellipse cx="380" cy="560" rx="360" ry="34" fill="#DDF0FC"/>'
              + I.window(210, 20, 240, 280) + I.plant(480, 280, 1.3) + I.bucket(50, 350, 1.4) + I.spray(290, 310, 1.3)
              + I.sponge(400, 486, .95) + I.bubble(40, 320, 24) + I.bubble(96, 290, 14) + I.bubble(700, 220, 18)
              + I.sparkle(170, 110, 22, I.SKY) + I.sparkle(640, 70, 15, I.SUN))
asset("live-cover-1_1080x1920", 1080, 1920, "fresh", f"""
<div class="glow" style="left:40px;top:560px;width:1000px;height:1000px"></div>
<div style="position:absolute;left:60px;right:60px;top:220px;display:flex;flex-direction:column;align-items:center;gap:44px;text-align:center">
  {logo("color", kind="stacked", width=300, descriptor="клининговая служба", gid="l1")}
  <h1 style="font-size:96px">Чистая квартира<br><em>без сюрпризов</em></h1>
</div>
{art(760, 620, LIVE_SCENE, 160, 700)}
<div style="position:absolute;left:60px;right:60px;top:1340px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center">{chips(TRUST[:2], 30, "14px 24px")}</div>
""")

PRICE_ROWS = [(I.sponge(14, 40, 1.1), "Поддерживающая", "от 2 400 ₽", "2-комн. — 3 900 ₽"),
              (I.spray(34, 6, .78), "Генеральная", "от 4 900 ₽", "2-комн. — 10 600 ₽"),
              (I.roller(20, 14, .78), "После ремонта", "от 6 200 ₽", "2-комн. — 13 700 ₽")]
rows = "".join(f"""<div class="card">{I.svg(150, 150, ill, "flex:none")}
  <div style="flex:1"><div style="font-size:44px;font-weight:800">{t}</div><div style="font-size:30px;font-weight:500;opacity:.75;margin-top:6px">{n}</div></div>
  <div style="font-size:46px;font-weight:800;color:#38BDF8;white-space:nowrap">{p}</div></div>""" for ill, t, p, n in PRICE_ROWS)
asset("live-cover-2_1080x1920", 1080, 1920, "navy", f"""
<div style="position:absolute;left:80px;right:80px;top:270px;display:flex;flex-direction:column;gap:34px">
  {logo(width=360, gid="l2")}
  <div class="kicker" style="font-size:30px;margin-top:30px">Тюмень · цены 2026</div>
  <h1 style="font-size:96px">Цена известна<br><em>до выезда</em></h1>
  <div style="display:flex;flex-direction:column;gap:22px;margin-top:10px">{rows}</div>
  <div style="font-size:30px;font-weight:500;opacity:.8">Мытьё окон — 350 ₽ за створку · химчистка мебели — 1 500 ₽ за предмет</div>
</div>""", ".card{display:flex;align-items:center;gap:28px;padding:22px 34px 22px 18px;border-radius:36px;background:rgba(255,255,255,.07);border:2px solid rgba(255,255,255,.14)}")

STEPS = [(I.stopwatch(12, 2, .95), "Напишите нам", "Ответим за 7 минут с точной ценой"),
         (I.bucket(2, 26, .95), "Приедем вовремя", "В 2-часовое окно, со своими средствами"),
         (I.phone_report(30, 4, .76), "Примите работу", "По фото и чек-листу — оплата после")]
steps = "".join(f"""<div class="step">{I.svg(150, 160, ill, "flex:none")}<div><div class="num">{i + 1}</div>
  <div style="font-size:48px;font-weight:800">{t}</div><div style="font-size:32px;font-weight:500;color:#334155;margin-top:8px">{d}</div></div></div>"""
                for i, (ill, t, d) in enumerate(STEPS))
asset("live-cover-3_1080x1920", 1080, 1920, "fresh", f"""
<div style="position:absolute;left:80px;right:80px;top:270px;display:flex;flex-direction:column;gap:34px">
  {logo("color", width=360, gid="l3")}
  <div class="kicker" style="font-size:30px;margin-top:30px;color:#0369A1">Как мы работаем</div>
  <h1 style="font-size:96px">Три шага<br>до <em>чистоты</em></h1>
  <div style="display:flex;flex-direction:column;gap:26px;margin-top:10px">{steps}</div>
</div>""", ".step{display:flex;align-items:center;gap:30px;padding:24px 30px;border-radius:36px;background:#fff;border:2px solid #DCEBF6;box-shadow:0 18px 40px rgba(3,105,161,.08)}"
           ".num{display:inline-block;font-size:24px;font-weight:800;color:#fff;background:#0EA5E9;border-radius:999px;padding:4px 16px;margin-bottom:10px}")

asset("live-cover-4_1080x1920", 1080, 1920, "sky", f"""
<div class="glow" style="left:90px;top:360px;width:900px;height:900px;opacity:.35"></div>
<div style="position:absolute;left:80px;right:80px;top:270px;display:flex;flex-direction:column;gap:34px;align-items:center;text-align:center">
  {logo("1c-white", width=360, gid="l4")}
  {I.svg(420, 470, I.shield(40, 20, 2.6) + I.sparkle(30, 380, 16) + I.sparkle(400, 300, 10), "margin-top:30px")}
  <h1 style="font-size:88px">Не понравилось —<br><span style="color:#0B2A4A">переуберём бесплатно</span></h1>
  <div style="font-size:38px;font-weight:700">в течение 24 часов после уборки</div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center">{chips(["Фотоотчёт до и после", "Работаем по чек-листу"], 30, "14px 24px")}</div>
</div>""")

asset("live-cover-5_1080x1920", 1080, 1920, "navy", f"""
<div style="position:absolute;left:80px;right:80px;top:270px;display:flex;flex-direction:column;gap:34px;align-items:center;text-align:center">
  {logo(width=360, gid="l5")}
  {I.svg(380, 420, I.stopwatch(20, 10, 2.45) + I.sparkle(350, 60, 16, I.SUN) + I.sparkle(20, 330, 10, I.PALE), "margin-top:40px")}
  <h1 style="font-size:100px">Расчёт<br><em>за 7 минут</em></h1>
  <div style="font-size:38px;font-weight:500;line-height:1.35;opacity:.9">Нажмите «Написать» и пришлите<br>площадь и тип уборки</div>
  <span class="pill" style="font-size:40px;padding:22px 44px">tyumen.cleanliness.pro</span>
</div>""")

# 3. Меню сообщества: 6 пунктов 752×512 (вдвое больше минимальных 376×256 — чётко на любых экранах)
MENU = [("menu-1-prices", "fresh", "Цены", "Студия — от 2 400 ₽", I.spray(150, 40, 1.15) + I.sponge(20, 190, 1.0) + I.bubble(60, 130, 22)),
        ("menu-2-order", "sky", "Расчёт<br>за 7 минут", "Напишите площадь", I.stopwatch(70, 40, 1.45) + I.sparkle(290, 50, 14)),
        ("menu-3-subscription", "navy", "Подписка<br>−15%", "Свой клинер раз в неделю", I.calendar(50, 60, 1.4) + I.sparkle(280, 50, 14, I.SUN)),
        ("menu-4-guarantee", "fresh", "Гарантия", "Переуберём за 24 часа", I.shield(70, 40, 1.45) + I.sparkle(40, 250, 10, I.SKY)),
        ("menu-5-gift", "sky", "Сертификаты", "На 5, 10 или 15 тысяч", I.gift(150, 0, 1.3)),
        ("menu-6-jobs", "navy", "Работа<br>у нас", "Ищем клинеров в Тюмени", I.bucket(20, 130, 1.25) + I.squeegee(150, 70, .95))]
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
    ("service-maintenance", "Поддерживающая уборка", "от 2 400 ₽", "Полы, пыль, кухня, санузел. Свой клинер по подписке −15%",
     I.spray(330, 40, 1.9) + I.sponge(90, 270, 1.7) + I.bubble(120, 120, 36) + I.bubble(190, 70, 20) + I.sparkle(620, 90, 26, I.SKY)),
    ("service-general", "Генеральная уборка", "от 4 900 ₽", "Налёт, жир, труднодоступные места. Фотоотчёт до и после",
     I.bucket(60, 130, 2.0) + I.spray(420, 40, 1.75) + I.sparkle(620, 70, 28, I.SUN) + I.sparkle(80, 80, 18, I.SKY)),
    ("service-post-renovation", "Уборка после ремонта", "от 6 200 ₽", "Строительная пыль, затирка, окна от плёнки",
     I.roller(70, 40, 1.75, -24) + I.bucket(360, 150, 1.8) + I.sparkle(640, 90, 24, I.SKY)),
    ("service-windows", "Мытьё окон", "350 ₽ / створка", "Без разводов. Вместе с уборкой — без доплаты за выезд",
     I.window(170, 10, 320, 360) + I.squeegee(470, 160, 1.6, -24) + I.sparkle(110, 90, 22, I.SKY)),
    ("service-upholstery", "Химчистка мебели", "1 500 ₽ / предмет", "Диваны, кресла, матрасы — на дому",
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
  <h1 style="font-size:80px">Уборка в Тюмени<br><em>с ценой до выезда</em></h1>
  <div style="display:grid;gap:20px;font-size:36px;font-weight:700;margin-top:8px">
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Расчёт за 7 минут в сообщениях</div>
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Свои средства и инвентарь</div>
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Оплата после приёмки работы</div>
    <div style="display:flex;gap:18px;align-items:center">{ck(46)}Не понравилось — переуберём за 24 ч</div>
  </div>
  <div style="display:grid;gap:10px;font-size:32px;font-weight:500;color:#334155;margin-top:14px;max-width:520px">
    <div>Поддерживающая — <b style="color:#0F172A">от 2 400 ₽</b></div><div>Генеральная — <b style="color:#0F172A">от 4 900 ₽</b></div>
    <div>После ремонта — <b style="color:#0F172A">от 6 200 ₽</b></div></div>
</div>
<span class="pill" style="position:absolute;left:84px;bottom:84px;font-size:36px;padding:20px 36px">Написать — расчёт за 7 минут</span>
""")

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


# 6. Примерный вид страницы сообщества (нейтральная рамка, не интерфейс VK) — для согласования.
#    Рендерятся последними: вставляют уже готовые PNG.
def img(name, style):
    return f'<img src="file://{OUT}/{name}.png" style="display:block;{style}">'


AVATAR = os.path.abspath(os.path.join(TOOLS, "..", "brand", "png", "vk-avatar_1000.png"))
NAME = "Точка Чистоты — клининг в Тюмени"
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
  <div style="height:860px;overflow:hidden;position:relative">{img("live-cover-1_1080x1920", "width:752px;margin-top:-60px")}
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
