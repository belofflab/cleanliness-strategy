"""Векторные иллюстрации в фирменном стиле: предметы уборки, интерьер, значки доверия (SVG-фрагменты).

Каждая функция рисует предмет в своей системе координат и возвращает <g>, сдвинутую в (x, y) и
масштабированную в s раз. Градиенты получают уникальные id, поэтому предметы можно повторять на одной странице.
Палитра — фирменные синие (brand/README.md) и два вспомогательных цвета только для иллюстраций:
зелёный для растений и тёплый жёлтый для губки и бликов солнца.
"""

from __future__ import annotations

import itertools

SKY, SKY2, MID, DEEP, NAVY, INK = "#0EA5E9", "#38BDF8", "#7DD3FC", "#0369A1", "#0B2A4A", "#0F172A"
LIGHT, ICE, PALE = "#E0F2FE", "#F0F9FF", "#BAE6FD"
LEAF, LEAF2, SUN, SUN2 = "#34D399", "#059669", "#FCD34D", "#F59E0B"

_ids = itertools.count(1)


def _uid() -> str:
    return f"i{next(_ids)}"


def lin(gid, c1, c2, x1=0, y1=0, x2=1, y2=1, o1=1, o2=1):
    return (f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{c1}" stop-opacity="{o1}"/><stop offset="1" stop-color="{c2}" stop-opacity="{o2}"/>'
            f'</linearGradient>')


def rad(gid, c1, c2, o1=1, o2=0, cx=.5, cy=.5, r=.5):
    return (f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="{c1}" stop-opacity="{o1}"/><stop offset="1" stop-color="{c2}" stop-opacity="{o2}"/>'
            f'</radialGradient>')


def g(x, y, s, body, rotate=0):
    rot = f" rotate({rotate})" if rotate else ""
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f}){rot}">{body}</g>'


def shadow(cx, cy, rx, ry, opacity=.16):
    u = _uid()
    return (f'<defs>{rad(u, NAVY, NAVY, opacity, 0)}</defs>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{u})"/>')


def sparkle(x, y, r, color=None, opacity=1):
    c = color or "#FFFFFF"
    k = .16 * r
    return (f'<path d="M{x},{y - r} Q{x + k},{y - k} {x + r},{y} Q{x + k},{y + k} {x},{y + r} '
            f'Q{x - k},{y + k} {x - r},{y} Q{x - k},{y - k} {x},{y - r}Z" fill="{c}" opacity="{opacity}"/>')


def bubble(x, y, r, opacity=1):
    u = _uid()
    return (f'<defs>{rad(u, "#FFFFFF", PALE, .95, .55, .38, .35, .7)}</defs>'
            f'<g opacity="{opacity}"><circle cx="{x}" cy="{y}" r="{r}" fill="url(#{u})" stroke="#FFFFFF" stroke-width="{max(1.2, r * .06):.1f}"/>'
            f'<path d="M{x - r * .55},{y - r * .2} A{r * .6},{r * .6} 0 0 1 {x - r * .1},{y - r * .62}" fill="none" '
            f'stroke="#FFFFFF" stroke-width="{max(1.5, r * .12):.1f}" stroke-linecap="round"/></g>')


def drop_mark(cx, cy, s, fill="#FFFFFF", dot=SKY):
    """Капля из знака (упрощённая), высота ≈ 2s."""
    return (f'<path d="M{cx},{cy - s} C{cx + s * .55},{cy - s * .25} {cx + s * .78},{cy + s * .12} {cx + s * .78},{cy + s * .42} '
            f'A{s * .78},{s * .78} 0 0 1 {cx - s * .78},{cy + s * .42} C{cx - s * .78},{cy + s * .12} {cx - s * .55},{cy - s * .25} {cx},{cy - s}Z" '
            f'fill="{fill}"/><circle cx="{cx}" cy="{cy + s * .42}" r="{s * .3}" fill="{dot}"/>')


# ——— предметы ———

def spray(x, y, s=1.0, rotate=0):
    """Распылитель с этикеткой-каплей. Коробка ≈ 100×175."""
    a, b, c = _uid(), _uid(), _uid()
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 1)}{lin(b, "#164E7E", NAVY, 0, 0, 0, 1)}{lin(c, "#FFFFFF", LIGHT, 0, 0, 0, 1)}</defs>'
            + shadow(51, 174, 44, 7)
            # распылённое облачко
            + "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PALE}" opacity="{o}"/>'
                      for cx, cy, r, o in ((2, 6, 3.2, .9), (-8, 2, 2.4, .7), (-6, 13, 2.6, .75), (-16, 8, 1.8, .55),
                                           (-14, -2, 1.5, .45), (-20, 15, 1.3, .4)))
            # курок и головка
            + f'<path d="M58,26 C60,40 66,48 72,56 C74,59 71,62 68,60 C60,54 54,44 52,30Z" fill="{NAVY}"/>'
            + f'<path d="M30,4 Q30,0 34,0 H72 Q80,0 80,8 V22 Q80,30 72,30 H40 Q30,30 30,22Z" fill="url(#{b})"/>'
            + f'<rect x="8" y="5" width="25" height="11" rx="4" fill="url(#{b})"/>'
            + '<rect x="38" y="4" width="34" height="5" rx="2.5" fill="#FFFFFF" opacity=".18"/>'
            # горлышко
            + f'<rect x="40" y="28" width="24" height="14" rx="3" fill="{NAVY}"/>'
            + '<rect x="38" y="36" width="28" height="7" rx="3" fill="#164E7E"/>'
            # корпус
            + f'<path d="M32,54 Q32,42 44,42 H60 Q72,42 72,54 L80,72 Q86,82 86,96 V162 Q86,175 73,175 H29 Q16,175 16,162 V96 '
              f'Q16,82 22,72Z" fill="url(#{a})"/>'
            + '<path d="M26,92 Q26,84 32,80" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" fill="none" opacity=".55"/>'
            + '<rect x="24" y="98" width="7" height="58" rx="3.5" fill="#FFFFFF" opacity=".32"/>'
            # этикетка
            + f'<rect x="34" y="102" width="42" height="50" rx="9" fill="url(#{c})"/>'
            + drop_mark(55, 122, 11, SKY, "#FFFFFF"))
    return g(x, y, s, body, rotate)


def bucket(x, y, s=1.0):
    """Ведро с пеной. Коробка ≈ 150×135."""
    a, b = _uid(), _uid()
    foam = "".join(bubble(cx, cy, r) for cx, cy, r in
                   ((30, 40, 15), (52, 30, 19), (78, 26, 21), (104, 32, 17), (122, 42, 12), (64, 44, 12), (94, 44, 13)))
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 1)}{lin(b, "#1E5F96", NAVY, 0, 0, 1, 0)}</defs>'
            + shadow(75, 134, 62, 8)
            + '<path d="M12,56 C12,-24 138,-24 138,56" fill="none" stroke="#94A3B8" stroke-width="4" stroke-linecap="round"/>'
            + foam
            + f'<path d="M12,58 H138 L124,124 Q122,133 113,133 H37 Q28,133 26,124Z" fill="url(#{a})"/>'
            + '<path d="M17,82 H133 L130,96 H20Z" fill="#FFFFFF" opacity=".16"/>'
            + f'<rect x="6" y="50" width="138" height="13" rx="6.5" fill="url(#{b})"/>'
            + '<rect x="30" y="70" width="6" height="52" rx="3" fill="#FFFFFF" opacity=".3"/>'
            + drop_mark(84, 101, 12, "#FFFFFF", SKY))
    return g(x, y, s, body)


def sponge(x, y, s=1.0, rotate=-8):
    """Губка с абразивным слоем. Коробка ≈ 110×70."""
    a, b = _uid(), _uid()
    pores = "".join(f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r * .8}" fill="{SUN2}" opacity=".35"/>'
                    for cx, cy, r in ((18, 40, 3), (34, 52, 2.4), (52, 42, 3.2), (70, 54, 2.2), (86, 42, 2.8),
                                      (28, 60, 1.8), (62, 60, 2), (94, 58, 1.8), (44, 34, 1.6), (78, 34, 1.6)))
    body = (f'<defs>{lin(a, "#FDE68A", SUN, 0, 0, 0, 1)}{lin(b, SKY, DEEP, 0, 0, 1, 1)}</defs>'
            + shadow(55, 70, 52, 6)
            + f'<rect x="2" y="24" width="106" height="44" rx="12" fill="url(#{a})"/>'
            + pores
            + f'<rect x="0" y="6" width="110" height="24" rx="10" fill="url(#{b})"/>'
            + '<rect x="8" y="10" width="60" height="5" rx="2.5" fill="#FFFFFF" opacity=".28"/>')
    return g(x, y, s, body, rotate)


def squeegee(x, y, s=1.0, rotate=-18):
    """Сгон для окон. Коробка ≈ 130×150."""
    a, b = _uid(), _uid()
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 0)}{lin(b, "#1E5F96", NAVY, 0, 0, 0, 1)}</defs>'
            + f'<rect x="56" y="30" width="18" height="118" rx="9" fill="url(#{a})"/>'
            + '<rect x="60" y="40" width="4" height="96" rx="2" fill="#FFFFFF" opacity=".35"/>'
            + f'<path d="M44,20 H86 L80,36 H50Z" fill="{NAVY}"/>'
            + f'<rect x="0" y="6" width="130" height="18" rx="6" fill="url(#{b})"/>'
            + f'<rect x="2" y="0" width="126" height="8" rx="4" fill="{MID}"/>')
    return g(x, y, s, body, rotate)


def window(x, y, w=220, h=260, s=1.0):
    """Окно с бликами и подоконником. Коробка ≈ (w+30)×(h+24)."""
    a, b = _uid(), _uid()
    gx, gy, gw, gh = 16, 16, w - 32, h - 32
    body = (f'<defs>{lin(a, "#C7EBFF", "#F2FAFF", 0, 0, 1, 1)}{lin(b, "#FFFFFF", "#E4EEF6", 0, 0, 0, 1)}</defs>'
            + f'<rect x="0" y="0" width="{w}" height="{h}" rx="14" fill="url(#{b})" stroke="#D6E4EF" stroke-width="2"/>'
            + f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="6" fill="url(#{a})"/>'
            # облака
            + f'<g fill="#FFFFFF" opacity=".95"><ellipse cx="{gx + gw * .3}" cy="{gy + gh * .3}" rx="{gw * .16}" ry="{gh * .045}"/>'
              f'<ellipse cx="{gx + gw * .24}" cy="{gy + gh * .27}" rx="{gw * .08}" ry="{gh * .045}"/>'
              f'<ellipse cx="{gx + gw * .74}" cy="{gy + gh * .58}" rx="{gw * .13}" ry="{gh * .035}"/></g>'
            # блики
            + f'<path d="M{gx + gw * .52},{gy} L{gx + gw * .72},{gy} L{gx + gw * .28},{gy + gh} L{gx + gw * .08},{gy + gh}Z" fill="#FFFFFF" opacity=".55"/>'
            + f'<path d="M{gx + gw * .8},{gy} L{gx + gw * .86},{gy} L{gx + gw * .42},{gy + gh} L{gx + gw * .36},{gy + gh}Z" fill="#FFFFFF" opacity=".6"/>'
            # переплёт
            + f'<rect x="{w / 2 - 6}" y="{gy}" width="12" height="{gh}" fill="url(#{b})"/>'
            + f'<rect x="{gx}" y="{h * .46}" width="{gw}" height="12" fill="url(#{b})"/>'
            + f'<rect x="{w / 2 + 12}" y="{h * .5}" width="6" height="22" rx="3" fill="#94A3B8"/>'
            # подоконник
            + f'<rect x="-15" y="{h - 4}" width="{w + 30}" height="18" rx="7" fill="#FFFFFF" stroke="#D6E4EF" stroke-width="2"/>'
            + sparkle(gx + gw * .62, gy + gh * .2, 14) + sparkle(gx + gw * .78, gy + gh * .32, 7))
    return g(x, y, s, body)


def plant(x, y, s=1.0):
    """Растение в горшке. Коробка ≈ 110×170."""
    a, b, c = _uid(), _uid(), _uid()
    leaves = [(-28, 60, 70), (-8, 54, 82), (12, 58, 74), (32, 62, 64), (-48, 66, 56), (50, 64, 52)]
    lv = "".join(f'<path d="M0,0 C{14},-{h * .35} {10},-{h * .8} 0,-{h} C-{10},-{h * .8} -{14},-{h * .35} 0,0Z" '
                 f'transform="translate(55,96) rotate({ang})" fill="url(#{a if i % 2 else b})"/>'
                 for i, (ang, _, h) in enumerate(leaves))
    body = (f'<defs>{lin(a, LEAF, LEAF2, 0, 0, 1, 1)}{lin(b, "#6EE7B7", LEAF, 0, 0, 1, 1)}{lin(c, "#FFFFFF", "#DCEAF5", 0, 0, 1, 1)}</defs>'
            + shadow(55, 168, 44, 6) + lv
            + f'<path d="M22,96 H88 L80,160 Q79,168 71,168 H39 Q31,168 30,160Z" fill="url(#{c})"/>'
            + f'<rect x="18" y="90" width="74" height="14" rx="7" fill="{DEEP}"/>'
            + '<rect x="30" y="112" width="5" height="44" rx="2.5" fill="#FFFFFF" opacity=".8"/>')
    return g(x, y, s, body)


def sofa(x, y, s=1.0):
    """Диван с подушками. Коробка ≈ 260×140."""
    a, b, c = _uid(), _uid(), _uid()
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 1)}{lin(b, "#5CC8F5", SKY, 0, 0, 0, 1)}{lin(c, "#FFE8A3", SUN, 0, 0, 1, 1)}</defs>'
            + shadow(130, 140, 120, 9)
            + f'<rect x="28" y="6" width="204" height="78" rx="26" fill="url(#{a})"/>'
            + f'<rect x="40" y="16" width="86" height="62" rx="20" fill="url(#{b})"/>'
            + f'<rect x="134" y="16" width="86" height="62" rx="20" fill="url(#{b})"/>'
            + f'<rect x="150" y="30" width="54" height="40" rx="12" fill="url(#{c})" transform="rotate(-8 177 50)"/>'
            + f'<rect x="20" y="70" width="220" height="44" rx="16" fill="url(#{a})"/>'
            + f'<rect x="36" y="66" width="188" height="22" rx="11" fill="url(#{b})"/>'
            + f'<rect x="0" y="42" width="46" height="78" rx="20" fill="url(#{a})"/>'
            + f'<rect x="214" y="42" width="46" height="78" rx="20" fill="url(#{a})"/>'
            + '<rect x="8" y="50" width="8" height="54" rx="4" fill="#FFFFFF" opacity=".3"/>'
            + f'<rect x="34" y="116" width="10" height="20" rx="3" fill="{NAVY}"/><rect x="216" y="116" width="10" height="20" rx="3" fill="{NAVY}"/>'
            + sparkle(70, 30, 9) + sparkle(84, 46, 5))
    return g(x, y, s, body)


def roller(x, y, s=1.0, rotate=-20):
    """Малярный валик. Коробка ≈ 150×170."""
    a, b = _uid(), _uid()
    body = (f'<defs>{lin(a, "#FFFFFF", "#CFE3F2", 0, 0, 0, 1)}{lin(b, SKY2, DEEP, 0, 0, 1, 0)}</defs>'
            + f'<rect x="10" y="0" width="130" height="50" rx="22" fill="url(#{a})" stroke="#C7D9E8" stroke-width="2"/>'
            + "".join(f'<rect x="{18 + i * 16}" y="6" width="3" height="38" rx="1.5" fill="#B9CFE0"/>' for i in range(8))
            + f'<path d="M140,25 H152 Q158,25 158,31 V62 Q158,68 152,68 H82 Q76,68 76,74 V92" fill="none" stroke="{NAVY}" stroke-width="7" stroke-linejoin="round"/>'
            + f'<rect x="64" y="90" width="24" height="78" rx="12" fill="url(#{b})"/>'
            + '<rect x="69" y="100" width="5" height="58" rx="2.5" fill="#FFFFFF" opacity=".35"/>')
    return g(x, y, s, body, rotate)


def keys(x, y, s=1.0, rotate=0):
    """Ключи от квартиры с брелоком. Коробка ≈ 150×170."""
    a, b = _uid(), _uid()

    def key(tx, ty, ang, color):
        return (f'<g transform="translate({tx},{ty}) rotate({ang})">'
                f'<circle cx="0" cy="0" r="18" fill="{color}"/><circle cx="0" cy="-4" r="6" fill="#FFFFFF"/>'
                f'<rect x="-5" y="14" width="10" height="70" rx="4" fill="{color}"/>'
                f'<rect x="5" y="56" width="12" height="8" rx="2" fill="{color}"/><rect x="5" y="70" width="9" height="8" rx="2" fill="{color}"/></g>')
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 1)}{lin(b, "#FFFFFF", LIGHT, 0, 0, 0, 1)}</defs>'
            + shadow(78, 168, 56, 6)
            + key(104, 62, -28, NAVY)
            + '<circle cx="74" cy="30" r="24" fill="none" stroke="#94A3B8" stroke-width="6"/>'
            + key(92, 58, -8, f"url(#{a})")
            + f'<g transform="rotate(16 52 50)"><rect x="24" y="48" width="56" height="80" rx="14" fill="url(#{b})" stroke="#D6E4EF" stroke-width="2"/>'
              f'<circle cx="52" cy="62" r="5" fill="#94A3B8"/>{drop_mark(52, 92, 14, SKY, "#FFFFFF")}</g>')
    return g(x, y, s, body, rotate)


def shield(x, y, s=1.0):
    """Щит с галочкой — гарантия. Коробка ≈ 130×150."""
    a, b = _uid(), _uid()
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 1)}{lin(b, "#FFFFFF", "#FFFFFF", 0, 0, 1, 1, .45, 0)}</defs>'
            + shadow(65, 150, 50, 7)
            + f'<path d="M65,0 L126,22 V70 C126,108 100,134 65,148 C30,134 4,108 4,70 V22Z" fill="url(#{a})"/>'
            + f'<path d="M65,0 L126,22 V70 C126,74 126,78 125,82 L65,30 Z" fill="url(#{b})"/>'
            + '<path d="M38,74 L58,94 L94,54" fill="none" stroke="#FFFFFF" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>'
            + sparkle(128, 6, 10, SUN) + sparkle(8, 120, 6, PALE))
    return g(x, y, s, body)


def calendar(x, y, s=1.0):
    """Календарь с отмеченными визитами — подписка. Коробка ≈ 150×150."""
    a = _uid()
    cells = ""
    for r in range(3):
        for c in range(4):
            cx, cy = 26 + c * 33, 66 + r * 26
            if (r, c) in ((0, 1), (1, 1), (2, 1)):
                cells += f'<circle cx="{cx}" cy="{cy}" r="11" fill="{SKY}"/><path d="M{cx - 5},{cy} l4,4 l7,-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            else:
                cells += f'<rect x="{cx - 8}" y="{cy - 6}" width="16" height="12" rx="4" fill="#DCE8F2"/>'
    body = (f'<defs>{lin(a, SKY, DEEP, 0, 0, 1, 1)}</defs>'
            + shadow(75, 150, 62, 7)
            + '<rect x="0" y="10" width="150" height="136" rx="18" fill="#FFFFFF" stroke="#D6E4EF" stroke-width="2"/>'
            + f'<path d="M0,28 Q0,10 18,10 H132 Q150,10 150,28 V44 H0Z" fill="url(#{a})"/>'
            + f'<rect x="34" y="0" width="10" height="24" rx="5" fill="{NAVY}"/><rect x="106" y="0" width="10" height="24" rx="5" fill="{NAVY}"/>'
            + cells)
    return g(x, y, s, body)


def gift(x, y, s=1.0):
    """Подарочная коробка — сертификат. Коробка ≈ 150×150."""
    a, b = _uid(), _uid()
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 1)}{lin(b, "#2B7FC0", NAVY, 0, 0, 1, 1)}</defs>'
            + shadow(75, 150, 62, 7)
            + f'<rect x="12" y="62" width="126" height="86" rx="12" fill="url(#{a})"/>'
            + f'<rect x="4" y="40" width="142" height="30" rx="10" fill="url(#{b})"/>'
            + '<rect x="66" y="40" width="18" height="108" fill="#FFFFFF"/>'
            + f'<rect x="12" y="70" width="126" height="6" fill="{NAVY}" opacity=".18"/>'
            + f'<path d="M75,40 C60,8 26,14 40,34 C46,42 62,42 75,40Z" fill="#FFFFFF" stroke="{LIGHT}" stroke-width="2"/>'
            + f'<path d="M75,40 C90,8 124,14 110,34 C104,42 88,42 75,40Z" fill="#FFFFFF" stroke="{LIGHT}" stroke-width="2"/>'
            + f'<circle cx="75" cy="40" r="8" fill="{SUN}"/>'
            + sparkle(140, 20, 10, SUN) + sparkle(18, 22, 6, PALE))
    return g(x, y, s, body)


def stopwatch(x, y, s=1.0, minutes=7):
    """Секундомер с сектором «7 минут». Коробка ≈ 140×160."""
    import math
    a = _uid()
    ang = minutes / 60 * 2 * math.pi
    ex, ey = 70 + 46 * math.sin(ang), 92 - 46 * math.cos(ang)
    body = (f'<defs>{lin(a, SKY2, DEEP, 0, 0, 1, 1)}</defs>'
            + shadow(70, 160, 56, 7)
            + f'<rect x="58" y="2" width="24" height="16" rx="5" fill="{NAVY}"/><rect x="64" y="14" width="12" height="12" fill="{NAVY}"/>'
            + f'<rect x="108" y="22" width="18" height="12" rx="4" fill="{NAVY}" transform="rotate(40 117 28)"/>'
            + f'<circle cx="70" cy="92" r="66" fill="url(#{a})"/>'
            + '<circle cx="70" cy="92" r="54" fill="#FFFFFF"/>'
            + f'<path d="M70,92 L70,46 A46,46 0 0 1 {ex:.1f},{ey:.1f}Z" fill="{PALE}"/>'
            + "".join(f'<rect x="68.5" y="42" width="3" height="{9 if i % 3 == 0 else 5}" rx="1.5" fill="#94A3B8" '
                      f'transform="rotate({i * 30} 70 92)"/>' for i in range(12))
            + f'<line x1="70" y1="92" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{NAVY}" stroke-width="6" stroke-linecap="round"/>'
            + f'<circle cx="70" cy="92" r="7" fill="{NAVY}"/>')
    return g(x, y, s, body)


def phone_report(x, y, s=1.0, rotate=-8):
    """Телефон с фотоотчётом «до / после». Коробка ≈ 110×200."""
    a, b = _uid(), _uid()
    dust = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#9CA3AF" opacity=".55"/>'
                   for cx, cy, r in ((22, 70, 3), (34, 96, 2.4), (18, 120, 2.8), (40, 136, 2), (28, 150, 3)))
    body = (f'<defs>{lin(a, "#D7DEE5", "#B8C2CC", 0, 0, 0, 1)}{lin(b, "#D9F2FF", "#F5FBFF", 0, 0, 0, 1)}</defs>'
            + f'<rect x="0" y="0" width="110" height="200" rx="20" fill="{NAVY}"/>'
            + f'<rect x="8" y="22" width="47" height="156" fill="url(#{a})"/>'
            + f'<rect x="55" y="22" width="47" height="156" fill="url(#{b})"/>' + dust
            + sparkle(78, 70, 9) + sparkle(88, 104, 6) + sparkle(72, 132, 7)
            + '<rect x="54" y="22" width="2" height="156" fill="#FFFFFF"/>'
            + '<rect x="14" y="160" width="34" height="13" rx="6.5" fill="#FFFFFF" opacity=".85"/>'
            + f'<rect x="60" y="160" width="38" height="13" rx="6.5" fill="{SKY}"/>'
            + '<rect x="40" y="8" width="30" height="6" rx="3" fill="#1E3A5F"/>')
    return g(x, y, s, body, rotate)


def building(x, y, s=1.0):
    """Новостройка. Коробка ≈ 170×240."""
    a, b = _uid(), _uid()
    wins = "".join(f'<rect x="{26 + c * 30}" y="{34 + r * 28}" width="18" height="16" rx="3" fill="{PALE if (r + c) % 3 else SUN}" '
                   f'opacity="{.95 if (r + c) % 3 else .9}"/>' for r in range(6) for c in range(4))
    body = (f'<defs>{lin(a, "#FFFFFF", "#D6E6F3", 0, 0, 1, 1)}{lin(b, SKY, DEEP, 0, 0, 0, 1)}</defs>'
            + shadow(85, 238, 82, 8)
            + f'<rect x="10" y="14" width="140" height="224" rx="8" fill="url(#{a})" stroke="#CBDCEA" stroke-width="2"/>'
            + f'<rect x="4" y="4" width="152" height="18" rx="6" fill="url(#{b})"/>' + wins
            + f'<rect x="62" y="204" width="36" height="34" rx="4" fill="{DEEP}"/>'
            + f'<circle cx="160" cy="214" r="18" fill="{LEAF}"/><rect x="157" y="222" width="6" height="16" fill="{LEAF2}"/>')
    return g(x, y, s, body)


def check_badge(x, y, r, color=SKY):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'
            f'<path d="M{x - r * .42},{y + r * .02} l{r * .3},{r * .3} l{r * .55},{-r * .6}" fill="none" stroke="#fff" '
            f'stroke-width="{r * .22:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')


def svg(w, h, body, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'style="{style}">{body}</svg>')
