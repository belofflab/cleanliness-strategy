"""Текст → SVG-контуры (кривые) фирменными шрифтами: Manrope (основной) и Unbounded (акцидентный).

Печатникам и вышивальщикам нужны файлы без живого текста: шрифт переводится
в кривые. Кернинг сохраняется — текст шейпится harfbuzz, глифы рисуются fontTools.
Шрифты лежат в marketing/fonts раздельными подмножествами (latin / cyrillic, знак ₽ — в latin-ext),
поэтому строка режется на прогоны по алфавиту.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from functools import lru_cache

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS = os.path.join(os.path.dirname(__file__), "..", "fonts")


@dataclass
class Outline:
    d: str
    width: float
    cap_height: float
    x_height: float
    ascent: float


@lru_cache(maxsize=None)
def _font(weight: int, subset: str, family: str = "manrope"):
    path = os.path.join(FONTS, f"{family}-{subset}-{weight}-normal.woff2")
    tt = TTFont(path)
    tt.flavor = None
    buf = io.BytesIO()
    tt.save(buf)
    data = buf.getvalue()
    tt = TTFont(io.BytesIO(data))
    hb_font = hb.Font(hb.Face(hb.Blob(data)))
    return tt, hb_font


def _subset_for(ch: str) -> str:
    if "Ѐ" <= ch <= "ӿ":
        return "cyrillic"
    if "₠" <= ch <= "⃀" and ch != "€":
        return "latin-ext"                      # знаки валют, в том числе ₽
    return "latin"


def _runs(text: str):
    runs: list[tuple[str, str]] = []
    for ch in text:
        # Пробел есть только в латинском подмножестве Manrope.
        subset = "latin" if ch.isspace() else _subset_for(ch)
        if runs and runs[-1][1] == subset:
            runs[-1] = (runs[-1][0] + ch, subset)
        else:
            runs.append((ch, subset))
    return runs


def outline(text: str, *, weight: int = 600, size: float = 100.0, x: float = 0.0, baseline: float = 0.0,
            tracking: float = 0.0, family: str = "manrope") -> Outline:
    """Контур строки: d-путь в координатах SVG, ширина и метрики в тех же единицах.

    tracking — межбуквенный интервал в долях кегля (0.02 = +2%).
    """
    cursor = x
    parts: list[str] = []
    tt_ref, _ = _font(weight, "latin", family)
    upem = tt_ref["head"].unitsPerEm
    scale = size / upem
    os2 = tt_ref["OS/2"]
    for run, subset in _runs(text):
        tt, hb_font = _font(weight, subset, family)
        glyph_set = tt.getGlyphSet()
        order = tt.getGlyphOrder()
        buf = hb.Buffer()
        buf.add_str(run)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf, {"kern": True, "liga": True})
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = order[info.codepoint]
            pen = SVGPathPen(glyph_set)
            gx = cursor + pos.x_offset * scale
            gy = baseline - pos.y_offset * scale
            glyph_set[name].draw(TransformPen(pen, (scale, 0, 0, -scale, gx, gy)))
            cmd = pen.getCommands()
            if cmd:
                parts.append(cmd)
            cursor += pos.x_advance * scale + tracking * size
    width = cursor - x - (tracking * size if text else 0)
    return Outline(
        d=" ".join(parts),
        width=width,
        cap_height=os2.sCapHeight * scale,
        x_height=os2.sxHeight * scale,
        ascent=tt_ref["hhea"].ascent * scale,
    )
