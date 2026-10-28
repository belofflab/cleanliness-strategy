"""Генерация 15 моушн-клипов для VK (HTML-сцены) и сценариев (scripts.md).

    python3 marketing/tools/build_clips.py          # HTML в marketing/video/src, сценарии в marketing/video/scripts.md
    node marketing/tools/render_clips.js            # кадры → немые MP4 1080×1920 в marketing/video/silent

Безопасные зоны VK Клипов: сверху ~200 px и снизу ~480 px — интерфейс, справа ~140 px — кнопки.
"""

from __future__ import annotations

import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import brandkit as B  # noqa: E402
from clips_data import CLIPS, END_CTA  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "video"))
SRC = os.path.join(ROOT, "src")

THEMES = {
    "navy": {"bg": "#0B2A4A", "ink": "#FFFFFF", "muted": "#B6C3D3", "accent": "#38BDF8", "card": "rgba(255,255,255,.08)",
             "line": "rgba(255,255,255,.14)", "blob1": "#0EA5E9", "blob2": "#0369A1", "pill": "#0EA5E9", "pill_ink": "#FFFFFF"},
    "light": {"bg": "#F4F8FB", "ink": "#0F172A", "muted": "#44546A", "accent": "#0369A1", "card": "#FFFFFF",
              "line": "#DDE6EF", "blob1": "#BAE6FD", "blob2": "#E0F2FE", "pill": "#0369A1", "pill_ink": "#FFFFFF"},
    "sky": {"bg": "#0786C7", "ink": "#FFFFFF", "muted": "#E0F2FE", "accent": "#0B2A4A", "card": "rgba(255,255,255,.16)",
            "line": "rgba(255,255,255,.24)", "blob1": "#38BDF8", "blob2": "#0369A1", "pill": "#0B2A4A", "pill_ink": "#FFFFFF"},
}

CSS = """
@font-face { font-family: Manrope; font-weight: 500; src: url(../../fonts/manrope-cyrillic-500-normal.woff2) format("woff2"); unicode-range: U+0400-04FF; }
@font-face { font-family: Manrope; font-weight: 500; src: url(../../fonts/manrope-latin-500-normal.woff2) format("woff2"); unicode-range: U+0000-03FF, U+2000-22FF; }
@font-face { font-family: Manrope; font-weight: 700; src: url(../../fonts/manrope-cyrillic-700-normal.woff2) format("woff2"); unicode-range: U+0400-04FF; }
@font-face { font-family: Manrope; font-weight: 700; src: url(../../fonts/manrope-latin-700-normal.woff2) format("woff2"); unicode-range: U+0000-03FF, U+2000-22FF; }
@font-face { font-family: Manrope; font-weight: 800; src: url(../../fonts/manrope-cyrillic-800-normal.woff2) format("woff2"); unicode-range: U+0400-04FF; }
@font-face { font-family: Manrope; font-weight: 800; src: url(../../fonts/manrope-latin-800-normal.woff2) format("woff2"); unicode-range: U+0000-03FF, U+2000-22FF; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1920px; overflow: hidden; }
body { background: var(--bg); color: var(--ink); font-family: Manrope, sans-serif; position: relative; }
.blob { position: absolute; border-radius: 50%; filter: blur(90px); opacity: .55; }
.b1 { width: 900px; height: 900px; background: var(--blob1); left: -260px; top: -180px; animation: drift1 var(--dur) linear both; }
.b2 { width: 820px; height: 820px; background: var(--blob2); right: -300px; bottom: 120px; animation: drift2 var(--dur) linear both; }
@keyframes drift1 { from { transform: translate(0, 0) scale(1); } to { transform: translate(160px, 260px) scale(1.15); } }
@keyframes drift2 { from { transform: translate(0, 0) scale(1.1); } to { transform: translate(-180px, -220px) scale(.95); } }
.wm { position: absolute; left: 72px; top: 212px; display: flex; align-items: center; gap: 18px; font-weight: 700; font-size: 34px;
      animation: fadeIn .5s .1s both; }
.wm svg { width: 64px; height: 64px; }
.wm span b { color: var(--accent); font-weight: 700; }
.stage { position: absolute; left: 72px; right: 140px; top: 330px; bottom: 500px; }
.scene { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; gap: 44px; opacity: 0;
         animation: sceneIn .35s var(--s) both, sceneOut .35s calc(var(--e) - .35s) forwards; }
.scene.top { justify-content: flex-start; padding-top: 40px; }
@keyframes sceneIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes sceneOut { from { opacity: 1; } to { opacity: 0; transform: translateY(-30px); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes up { from { opacity: 0; transform: translateY(46px); } to { opacity: 1; transform: none; } }
@keyframes pop { 0% { opacity: 0; transform: scale(.6); } 70% { opacity: 1; transform: scale(1.08); } 100% { opacity: 1; transform: scale(1); } }
@keyframes sweep { from { background-size: 0% 18px; } to { background-size: 100% 18px; } }
.in { animation: up .7s cubic-bezier(.2,.8,.2,1) calc(var(--s) + var(--d)) both; }
.kicker { font-size: 34px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.h1 { font-size: 104px; line-height: 1.04; font-weight: 800; letter-spacing: -.02em; }
.h1 em { font-style: normal; color: var(--accent);
         background: linear-gradient(var(--accent), var(--accent)) no-repeat 0 92% / 0% 18px;
         background-image: linear-gradient(color-mix(in srgb, var(--accent) 28%, transparent), color-mix(in srgb, var(--accent) 28%, transparent));
         animation: sweep .8s ease-out calc(var(--s) + var(--d) + .5s) both; }
.note { font-size: 38px; line-height: 1.35; font-weight: 500; color: var(--muted); max-width: 820px; }
.list { display: flex; flex-direction: column; gap: 26px; }
.item { display: flex; align-items: center; gap: 28px; font-size: 48px; line-height: 1.2; font-weight: 700;
        background: var(--card); border: 2px solid var(--line); border-radius: 30px; padding: 26px 32px; }
.ico { flex: none; width: 64px; height: 64px; border-radius: 50%; display: grid; place-items: center; background: var(--pill); color: var(--pill_ink);
       font-size: 34px; font-weight: 800; animation: pop .5s calc(var(--s) + var(--d) + .25s) both; }
.ico.no { background: #E11D48; }
.ico svg { width: 36px; height: 36px; }
.prices { background: var(--card); border: 2px solid var(--line); border-radius: 36px; padding: 18px 40px; }
.row { display: flex; justify-content: space-between; align-items: baseline; gap: 24px; padding: 26px 0; font-size: 50px; font-weight: 700; }
.row + .row { border-top: 2px solid var(--line); }
.row b { font-weight: 800; color: var(--accent); white-space: nowrap; }
.big { display: flex; flex-direction: column; gap: 10px; }
.big b { font-size: 230px; line-height: .95; font-weight: 800; letter-spacing: -.04em; animation: pop .8s calc(var(--s) + var(--d)) both; display: inline-block; }
.big span { font-size: 44px; font-weight: 700; color: var(--muted); }
.chips { display: flex; flex-wrap: wrap; gap: 18px; }
.chip { font-size: 42px; font-weight: 700; padding: 20px 32px; border-radius: 999px; background: var(--card); border: 2px solid var(--line); }
.end { position: absolute; left: 72px; right: 140px; top: 300px; bottom: 480px; display: flex; flex-direction: column; align-items: center;
       justify-content: center; gap: 40px; text-align: center; opacity: 0; animation: sceneIn .4s var(--s) both; }
.end .logo { width: 560px; animation: pop .9s calc(var(--s) + .1s) both; }
.end .t { font-size: 76px; font-weight: 800; animation: up .6s calc(var(--s) + .5s) both; }
.end .url { font-size: 46px; font-weight: 800; padding: 22px 40px; border-radius: 999px; background: var(--pill); color: var(--pill_ink);
            animation: up .6s calc(var(--s) + .7s) both; }
.end .sub { font-size: 36px; font-weight: 500; color: var(--muted); animation: up .6s calc(var(--s) + .9s) both; }
"""

CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
CROSS = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>'


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def accent(s: str) -> str:
    return re.sub(r"\[(.+?)\]", lambda m: f"<em>{m.group(1)}</em>", esc(s))


def block(kind, args, d):
    """HTML блока сцены; d — задержка появления от начала сцены, с. Возвращает (html, следующая задержка)."""
    if kind == "kicker":
        return f'<div class="kicker in" style="--d:{d:.2f}s">{esc(args[0])}</div>', d + 0.15
    if kind == "h1":
        return f'<div class="h1 in" style="--d:{d:.2f}s">{accent(args[0])}</div>', d + 0.35
    if kind == "note":
        return f'<div class="note in" style="--d:{d:.2f}s">{esc(args[0])}</div>', d + 0.3
    if kind in ("checks", "steps"):
        items = []
        for i, text in enumerate(args[0]):
            if kind == "steps":
                icon = f'<span class="ico" style="--d:{d:.2f}s">{i + 1}</span>'
            elif text.startswith("✕"):
                icon, text = f'<span class="ico no" style="--d:{d:.2f}s">{CROSS}</span>', text[1:].strip()
            else:
                icon, text = f'<span class="ico" style="--d:{d:.2f}s">{CHECK}</span>', text.lstrip("✓").strip()
            items.append(f'<div class="item in" style="--d:{d:.2f}s">{icon}<span>{esc(text)}</span></div>')
            d += 0.55
        return f'<div class="list">{"".join(items)}</div>', d
    if kind == "prices":
        rows = []
        for label, value in args[0]:
            rows.append(f'<div class="row in" style="--d:{d:.2f}s"><span>{esc(label)}</span><b>{esc(value)}</b></div>')
            d += 0.45
        return f'<div class="prices">{"".join(rows)}</div>', d
    if kind == "big":
        return (f'<div class="big"><b style="--d:{d:.2f}s">{esc(args[0])}</b>'
                f'<span class="in" style="--d:{d + 0.4:.2f}s">{esc(args[1])}</span></div>'), d + 0.8
    if kind == "chips":
        chips = []
        for text in args[0]:
            chips.append(f'<span class="chip in" style="--d:{d:.2f}s">{esc(text)}</span>')
            d += 0.3
        return f'<div class="chips">{"".join(chips)}</div>', d
    raise ValueError(kind)


def clip_html(c) -> str:
    t = THEMES[c["theme"]]
    dur = c["duration"]
    variables = ";".join(f"--{k}:{v}" for k, v in t.items()) + f";--dur:{dur}s"
    scenes = []
    for t0, t1, blocks in c["scenes"]:
        d, parts = 0.15, []
        for kind, *args in blocks:
            h, d = block(kind, args, d)
            parts.append(h)
        top = " top" if any(k in ("checks", "steps", "prices") for k, *_ in blocks) and len(blocks) > 1 else ""
        scenes.append(f'<section class="scene{top}" style="--s:{t0:.2f}s;--e:{t1:.2f}s">{"".join(parts)}</section>')
    end_start = max(t1 for _, t1, _ in c["scenes"]) + 0.15
    scheme = "color" if c["theme"] == "light" else "color-dark"
    logo_body, lw, lh = B.stacked(scheme, m=140, descriptor="клининговая служба", gid=f"g{c['id']}")
    logo = B.svg_doc(logo_body, lw, lh, pad=4).replace("<svg ", '<svg class="logo" ', 1)
    if c["theme"] == "sky":
        logo_body, lw, lh = B.stacked("1c-white", m=140, descriptor="клининговая служба")
        logo = B.svg_doc(logo_body, lw, lh, pad=4).replace("<svg ", '<svg class="logo" ', 1)
    end = (f'<section class="end" style="--s:{end_start:.2f}s">{logo}'
           f'<div class="t">{esc(END_CTA["title"])}</div><div class="url">{esc(END_CTA["url"])}</div>'
           f'<div class="sub">{esc(END_CTA["sub"])}</div></section>')
    mark = B.svg_doc(B.mark(0, 0, 32, "color", gid=f"w{c['id']}"), 32, 32)
    if c["theme"] == "sky":
        mark = B.svg_doc(B.mark(0, 0, 32, "onecolor", color="#FFFFFF"), 32, 32)
    wm = f'<div class="wm">{mark}<span>Точка <b>Чистоты</b></span></div>'
    return (f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>{c["id"]:02d} {esc(c["slug"])}</title>'
            f'<link rel="stylesheet" href="clip.css"></head>'
            f'<body style="{variables}" data-duration="{dur}"><div class="blob b1"></div><div class="blob b2"></div>{wm}'
            f'<div class="stage">{"".join(scenes)}</div>{end}</body></html>\n')


def scripts_md() -> str:
    out = ["# 15 клипов для VK: сценарии, промпты для ИИ-видео, подписи", "",
           "Каждый клип есть в двух видах:", "",
           "1. **Готовый моушн-клип** `mp4/NN-slug.mp4` (1080×1920, 30 к/с) — можно публиковать сразу.",
           "   Нежная фоновая музыка уже сведена: она синтезирована с нуля (`tools/music.py`), прав третьих лиц нет.",
           "   Женский голос (Yandex SpeechKit, текст из поля «Голос») накладывает `tools/voiceover.py`.",
           "2. **ИИ-версия** — промпт ниже для генератора видео (Шедеврум или Kandinsky — по-русски; Kling, Runway, Hailuo — по-английски).",
           "   Сгенерированный ролик 5–10 с монтируйте с концовкой из моушн-клипа (последние 3 с — логотип и призыв).",
           "",
           "Голос можно и записать — менеджером: положите файл `audio/voice/NN-slug.ogg` и запустите `voiceover.py`.",
           "В ИИ-кадрах не показывайте лица реальных клиентов и чужие логотипы; форма в промптах — тёмно-синяя с логотипом-каплей.",
           ""]
    for c in CLIPS:
        headline = re.sub(r"[\[\]]", "", c["scenes"][0][2][-1][1])
        out += [f"## {c['id']:02d}. {c['rubric']}: {headline}", "",
                f"- **Файл:** `mp4/{c['id']:02d}-{c['slug']}.mp4` · {c['duration']} с · когда публиковать: {c['publish']}",
                f"- **Крючок (первые 2 секунды):** {c['hook']}",
                f"- **Голос:** {c['voiceover']}",
                f"- **Подпись в VK:** {c['caption']}",
                f"- **Хештеги:** {c['tags']} #точкачистоты",
                "- **Текст в кадре:**"]
        for t0, t1, blocks in c["scenes"]:
            texts = []
            for kind, *args in blocks:
                if kind in ("kicker", "h1", "note"):
                    texts.append(re.sub(r"[\[\]]", "", args[0]))
                elif kind in ("checks", "steps", "chips"):
                    texts.append(" · ".join(a.lstrip("✓✕ ").strip() for a in args[0]))
                elif kind == "prices":
                    texts.append(" · ".join(f"{a} — {b}" for a, b in args[0]))
                elif kind == "big":
                    texts.append(f"{args[0]} — {args[1]}")
            out.append(f"  - {t0:.1f}–{t1:.1f} с: {' / '.join(texts)}")
        out += [f"  - концовка: логотип · «{END_CTA['title']}» · {END_CTA['url']}",
                f"- **Промпт ИИ (RU):** {c['ai_ru']}",
                f"- **Промпт ИИ (EN):** {c['ai_en']}", ""]
    return "\n".join(out)


def build():
    os.makedirs(SRC, exist_ok=True)
    with open(os.path.join(SRC, "clip.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    for c in CLIPS:
        with open(os.path.join(SRC, f"{c['id']:02d}-{c['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(clip_html(c))
    with open(os.path.join(ROOT, "scripts.md"), "w", encoding="utf-8") as f:
        f.write(scripts_md())
    print(f"{len(CLIPS)} клипов → {SRC}")


if __name__ == "__main__":
    build()
