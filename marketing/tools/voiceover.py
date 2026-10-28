"""Озвучка клипов голосом Yandex SpeechKit и сведение с фоновой музыкой.

    export YANDEX_SPEECHKIT_API_KEY=...        # API-ключ сервисного аккаунта (не коммитить!)
    export YANDEX_FOLDER_ID=...                # необязательно для ключа сервисного аккаунта
    python3 marketing/tools/voiceover.py               # голос + музыка для всех клипов
    python3 marketing/tools/voiceover.py --music-only  # только музыка (без ключа)
    python3 marketing/tools/voiceover.py 1 7 15        # отдельные клипы

Текст «Голоса» делится на крючок для первой сцены и текст для второй (после первой фразы или по «|»). Части
синтезируются отдельно и кэшируются в marketing/audio/voice/NN-slug.1.ogg и NN-slug.2.ogg — туда же можно положить
запись голоса менеджера, ключ для неё не нужен. Сцены растягиваются под речь (marketing/video/timing.json), немые
клипы перерисовываются, музыка приглушается под голос (sidechain), итог нормализуется до −14 LUFS.
Голос по умолчанию — alena, эмоция good, темп 1,1; меняются переменными SPEECHKIT_VOICE, SPEECHKIT_EMOTION, SPEECHKIT_SPEED.
Немые исходники — marketing/video/silent, результат — marketing/video/mp4.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import build_clips  # noqa: E402
import music  # noqa: E402
from clips_data import CLIPS  # noqa: E402

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(TOOLS, ".."))
SILENT = os.path.join(BASE, "video", "silent")
FINAL = os.path.join(BASE, "video", "mp4")
VOICE = os.path.join(BASE, "audio", "voice")
MUSIC = os.path.join(BASE, "audio", "music")

TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
LEAD = 0.35   # с: фраза вступает после появления заголовка сцены
GAP = 0.45    # с: пауза между концом фразы и сменой сцены

MUSIC_BY_RUBRIC = {"Цены без сюрпризов": "morning", "Как мы работаем": "morning", "Лайфхак клинера": "fresh",
                   "Новостройки Тюмени": "cozy", "Акции": "cozy", "Знакомство": "morning"}


def tts_text(text: str) -> str:
    """Числа с пробелами-разделителями («13 700») синтезатор читает как два числа — склеиваем."""
    return re.sub(r"(?<=\d)[   ](?=\d{3}\b)", "", text)


def parts(clip) -> list[str]:
    """Крючок для первой сцены и текст для второй: по «|», иначе после первой фразы."""
    text = clip["voiceover"]
    head, sep, tail = text.partition("|")
    if not sep:
        head, _, tail = (re.split(r"(?<=[.?!])(\s+)", text, maxsplit=1) + ["", ""])[:3]
    return [head.strip(), tail.strip()]


def part_paths(clip) -> list[str]:
    return [os.path.join(VOICE, f"{clip['id']:02d}-{clip['slug']}.{i}.ogg") for i in (1, 2)]


def silent(clip) -> str:
    return os.path.join(SILENT, f"{clip['id']:02d}-{clip['slug']}.mp4")


def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def synthesize(text: str, path: str):
    key = os.environ["YANDEX_SPEECHKIT_API_KEY"]
    params = {"text": tts_text(text), "lang": "ru-RU", "voice": os.environ.get("SPEECHKIT_VOICE", "alena"),
              "emotion": os.environ.get("SPEECHKIT_EMOTION", "good"), "speed": os.environ.get("SPEECHKIT_SPEED", "1.1"),
              "format": "oggopus"}
    if os.environ.get("YANDEX_FOLDER_ID"):
        params["folderId"] = os.environ["YANDEX_FOLDER_ID"]
    req = urllib.request.Request(TTS_URL, data=urllib.parse.urlencode(params).encode(),
                                 headers={"Authorization": f"Api-Key {key}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                audio = resp.read()
            break
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
    with open(path + ".part", "wb") as f:
        f.write(audio)
    os.replace(path + ".part", path)


def voice(clip) -> list[tuple[str, float]]:
    """Части голоса клипа (кэш в audio/voice): [(путь, длина)] по сценам."""
    os.makedirs(VOICE, exist_ok=True)
    out = []
    for text, path in zip(parts(clip), part_paths(clip)):
        if not os.path.exists(path):
            synthesize(text, path)
        out.append((path, duration(path)))
    return out


def retime(clip, voiced) -> dict:
    """Каждая сцена длится не меньше своей фразы; концовка с логотипом сохраняет прежнюю длину."""
    t, scenes = 0.0, []
    for (t0, t1, _), (_, length) in zip(clip["scenes"], voiced):
        t1 = round(t + max(t1 - t0, LEAD + length + GAP), 2)
        scenes.append([round(t, 2), t1])
        t = t1
    return {"scenes": scenes, "duration": round(t + clip["duration"] - clip["scenes"][-1][1], 2)}


def mix(clip, voiced=None, timing=None):
    name = f"{clip['id']:02d}-{clip['slug']}"
    src = silent(clip)
    track = os.path.join(MUSIC, f"{MUSIC_BY_RUBRIC.get(clip['rubric'], 'morning')}.wav")
    total = duration(src)
    music_chain = f"[1:a]atrim=0:{total:.3f},afade=t=in:d=0.5,afade=t=out:st={max(0.0, total - 1.4):.3f}:d=1.4"
    if voiced:
        delays = "".join(f"[{i + 2}:a]adelay={int((t0 + LEAD) * 1000)}:all=1[p{i}];"
                         for i, (t0, _) in enumerate(timing["scenes"]))
        labels = "".join(f"[p{i}]" for i in range(len(voiced)))
        graph = (f"{delays}{labels}amix=inputs={len(voiced)}:duration=longest:normalize=0,highpass=f=80,"
                 f"acompressor=threshold=0.1:ratio=3:attack=5:release=120,apad=whole_dur={total:.3f},asplit=2[v1][v2];"
                 f"{music_chain},volume=0.55[m];[m][v1]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=400[md];"
                 f"[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        graph = f"{music_chain},loudnorm=I=-16:TP=-1.5:LRA=11[a]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", track]
    for path, _ in voiced or []:
        cmd += ["-i", path]
    cmd += ["-filter_complex", graph, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-t", f"{total:.3f}", "-movflags", "+faststart", os.path.join(FINAL, f"{name}.mp4")]
    subprocess.run(cmd, check=True)
    return name, total


def main(argv):
    music_only = "--music-only" in argv
    ids = [int(a) for a in argv if a.isdigit()]
    clips = [c for c in CLIPS if not ids or c["id"] in ids]
    timing = build_clips.load_timing()
    voiced = {}
    if not music_only:
        unvoiced = [c for c in clips if not all(os.path.exists(p) for p in part_paths(c))]
        if unvoiced and not os.environ.get("YANDEX_SPEECHKIT_API_KEY"):
            sys.exit("Нет YANDEX_SPEECHKIT_API_KEY и готового голоса для клипов "
                     f"{', '.join(str(c['id']) for c in unvoiced)} — задайте ключ или запустите с --music-only")
        for c in clips:
            voiced[c["id"]] = voice(c)
            timing[str(c["id"])] = retime(c, voiced[c["id"]])
        with open(build_clips.TIMING, "w", encoding="utf-8") as f:  # по строке на клип — читаемый diff
            rows = (f' "{k}": {json.dumps(v)}' for k, v in sorted(timing.items(), key=lambda kv: int(kv[0])))
            f.write("{\n" + ",\n".join(rows) + "\n}\n")
        build_clips.build()
    # немые клипы, нарисованные под другой тайминг, перерисовываются
    stale = [c["id"] for c in clips if str(c["id"]) in timing and (
        not os.path.exists(silent(c)) or abs(duration(silent(c)) - timing[str(c["id"])]["duration"]) > 0.05)]
    if stale:
        subprocess.run(["node", os.path.join(TOOLS, "render_clips.js"), *map(str, stale)], check=True)
    if not all(os.path.exists(os.path.join(MUSIC, f"{n}.wav")) for n in music.TRACKS):
        music.build()
    os.makedirs(FINAL, exist_ok=True)
    for clip in clips:
        if not os.path.exists(silent(clip)):
            print(f"{clip['id']:02d}: нет немого исходника — сначала render_clips.js")
            continue
        name, total = mix(clip, voiced.get(clip["id"]), timing.get(str(clip["id"])))
        print(f"{name}.mp4 — {total:.1f} с, {'голос + музыка' if clip['id'] in voiced else 'музыка'}")


if __name__ == "__main__":
    main(sys.argv[1:])
