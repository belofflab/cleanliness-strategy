"""Фирменные элементы «Точки Чистоты» как SVG-фрагменты.

Знак взят из сайта (apps/web/app/icon.svg, apps/web/components/Logo.jsx):
скруглённый квадрат с градиентом, капля с точкой и искра. Словесная часть —
Manrope SemiBold, «Точка» тёмным, «Чистоты» фирменным синим, как в шапке сайта.
Все тексты переводятся в кривые (textpath.outline).
"""

from __future__ import annotations

from textpath import outline

SKY = "#0EA5E9"
DEEP = "#0369A1"
LIGHT = "#E0F2FE"
INK = "#0F172A"
MUTED = "#5F6B7A"
WHITE = "#FFFFFF"
SKY_ON_DARK = "#38BDF8"
NAVY = "#0B2A4A"

# Геометрия знака в единицах 32×32 (как в icon.svg).
DROP = "M16 5.8c3.9 4.4 6.3 7.6 6.3 10.8a6.3 6.3 0 1 1-12.6 0c0-3.2 2.4-6.4 6.3-10.8Z"
SPARK = "M24.6 4.4l.62 1.58 1.58.62-1.58.62-.62 1.58-.62-1.58-1.58-.62 1.58-.62.62-1.58Z"
SQUARE = "M9 0H23A9 9 0 0 1 32 9V23A9 9 0 0 1 23 32H9A9 9 0 0 1 0 23V9A9 9 0 0 1 9 0Z"
DOT = (16, 17.1, 2.4)


def gradient_def(gid: str) -> str:
    return (f'<linearGradient id="{gid}" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">'
            f'<stop stop-color="{SKY}"/><stop offset="1" stop-color="{DEEP}"/></linearGradient>')


def mark(x: float, y: float, size: float, variant: str = "color", gid: str = "tc-grad", color: str | None = None) -> str:
    """Знак. variant: color — полноцветный; onecolor — одним цветом (капля и искра — вырез)."""
    s = size / 32
    cx, cy, r = DOT
    if variant == "color":
        body = (f'<defs>{gradient_def(gid)}</defs>'
                f'<path d="{SQUARE}" fill="url(#{gid})"/>'
                f'<path d="{DROP}" fill="{WHITE}"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SKY}"/>'
                f'<path d="{SPARK}" fill="{LIGHT}"/>')
    else:
        c = color or DEEP
        body = (f'<path d="{SQUARE} {DROP} {SPARK}" fill="{c}" fill-rule="evenodd"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}"/>')
    return f'<g transform="translate({x:.3f} {y:.3f}) scale({s:.5f})">{body}</g>'


def wordmark(x: float, baseline: float, size: float, c1: str, c2: str, weight: int = 600):
    """«Точка Чистоты» в кривых. Возвращает (svg, ширина, высота прописной)."""
    first = outline("Точка ", weight=weight, size=size, x=x, baseline=baseline)
    second = outline("Чистоты", weight=weight, size=size, x=x + first.width, baseline=baseline)
    svg = f'<path d="{first.d}" fill="{c1}"/><path d="{second.d}" fill="{c2}"/>'
    return svg, first.width + second.width, first.cap_height


def text(s: str, x: float, baseline: float, size: float, color: str, weight: int = 500, tracking: float = 0.0,
         anchor: str = "start"):
    """Произвольная строка в кривых; anchor: start | middle | end."""
    o = outline(s, weight=weight, size=size, x=0, baseline=baseline, tracking=tracking)
    dx = {"start": x, "middle": x - o.width / 2, "end": x - o.width}[anchor]
    o = outline(s, weight=weight, size=size, x=dx, baseline=baseline, tracking=tracking)
    return f'<path d="{o.d}" fill="{color}"/>', o.width, o.cap_height, o.x_height


SCHEMES = {
    # name: (mark variant, mark color, word color 1, word color 2, descriptor color)
    "color": ("color", None, INK, DEEP, MUTED),
    "color-dark": ("color", None, WHITE, SKY_ON_DARK, "#B6C3D3"),
    "1c-blue": ("onecolor", DEEP, DEEP, DEEP, DEEP),
    "1c-white": ("onecolor", WHITE, WHITE, WHITE, WHITE),
    "1c-black": ("onecolor", INK, INK, INK, INK),
}


def horizontal(scheme: str, m: float = 120.0, descriptor: str | None = None, gid: str = "tc-grad"):
    """Горизонтальный логотип. Возвращает (svg-тело, ширина, высота)."""
    mv, mc, c1, c2, cd = SCHEMES[scheme]
    gap = m * 0.26
    size = m * 0.5
    probe = outline("Т", size=size)
    cap = probe.cap_height
    if descriptor:
        dsize = size * 0.42
        dprobe = outline("к", weight=500, size=dsize)
        block = cap + size * 0.34 + dprobe.x_height
        top = (m - block) / 2
        base = top + cap
        dbase = base + size * 0.34 + dprobe.x_height
    else:
        base = (m + cap) / 2
    word, ww, _ = wordmark(m + gap, base, size, c1, c2)
    parts = [mark(0, 0, m, mv, gid, mc), word]
    width = m + gap + ww
    if descriptor:
        d, dw, _, _ = text(descriptor, m + gap + size * 0.03, dbase, dsize, cd, weight=500, tracking=0.04)
        parts.append(d)
        width = max(width, m + gap + dw)
    return "".join(parts), width, m


def stacked(scheme: str, m: float = 140.0, descriptor: str | None = None, extra: str | None = None,
            gid: str = "tc-grad"):
    """Вертикальный логотип: знак над надписью, всё по центру."""
    mv, mc, c1, c2, cd = SCHEMES[scheme]
    size = m * 0.36
    _, ww, cap = wordmark(0, 0, size, c1, c2)
    width = max(m, ww)
    cx = width / 2
    parts = [mark(cx - m / 2, 0, m, mv, gid, mc)]
    base = m + m * 0.2 + cap
    word, _, _ = wordmark(cx - ww / 2, base, size, c1, c2)
    parts.append(word)
    height = base + size * 0.1
    if descriptor:
        dsize = size * 0.44
        d, dw, dcap, dx = text(descriptor, cx, base + size * 0.62, dsize, cd, weight=500, tracking=0.04, anchor="middle")
        parts.append(d)
        width = max(width, dw)
        height = base + size * 0.62 + size * 0.05
    if extra:
        esize = size * 0.5
        e, ew, ecap, _ = text(extra, cx, height + esize * 1.25, esize, cd if scheme != "color" else DEEP, weight=600,
                              anchor="middle")
        parts.append(e)
        width = max(width, ew)
        height = height + esize * 1.35
    if width > max(m, ww):
        # Перецентровать, если подпись шире надписи.
        shift = (width - max(m, ww)) / 2
        return f'<g transform="translate({shift:.3f} 0)">{"".join(parts)}</g>', width, height
    return "".join(parts), width, height


def svg_doc(body: str, width: float, height: float, pad: float = 0.0, bg: str | None = None,
            unit: str = "", title: str = "") -> str:
    vw, vh = width + 2 * pad, height + 2 * pad
    size_attr = f'width="{vw:.2f}{unit}" height="{vh:.2f}{unit}"' if unit else f'width="{vw:.0f}" height="{vh:.0f}"'
    bg_rect = f'<rect x="{-pad:.2f}" y="{-pad:.2f}" width="{vw:.2f}" height="{vh:.2f}" fill="{bg}"/>' if bg else ""
    t = f"<title>{title}</title>" if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" {size_attr} viewBox="{-pad:.2f} {-pad:.2f} {vw:.2f} {vh:.2f}">'
            f'{t}{bg_rect}{body}</svg>\n')
