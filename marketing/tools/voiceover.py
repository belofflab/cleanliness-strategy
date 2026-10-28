"""Озвучка клипов голосом Yandex SpeechKit и сведение с фоновой музыкой.

    export YANDEX_SPEECHKIT_API_KEY=...        # API-ключ сервисного аккаунта (не коммитить!)
    export YANDEX_FOLDER_ID=...                # необязательно для ключа сервисного аккаунта
    python3 marketing/tools/voiceover.py               # голос + музыка для всех клипов
    python3 marketing/tools/voiceover.py --music-only  # только музыка (без ключа)
    python3 marketing/tools/voiceover.py 1 7 15        # отдельные клипы

Голос по умолчанию — alena (эмоция good), меняется переменными SPEECHKIT_VOICE, SPEECHKIT_EMOTION.
Готовый голос (кэш синтеза или запись менеджера) берётся из marketing/audio/voice/NN-slug.ogg — ключ для него не нужен.
Если текст не помещается в клип, речь ускоряется (до 1,25×), а если и этого мало — последний кадр
клипа продлевается. Музыка приглушается под голос (sidechain), итог нормализуется до −14 LUFS.
Немые исходники — marketing/video/silent, результат — marketing/video/mp4.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import music  # noqa: E402
from clips_data import CLIPS  # noqa: E402

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SILENT = os.path.join(BASE, "video", "silent")
FINAL = os.path.join(BASE, "video", "mp4")
VOICE = os.path.join(BASE, "audio", "voice")
MUSIC = os.path.join(BASE, "audio", "music")

TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
VOICE_START = 0.35   # с: голос начинается после появления заголовка
TAIL = 0.6           # с: тишина голоса до конца клипа
MAX_SPEED = 1.25

MUSIC_BY_RUBRIC = {"Цены без сюрпризов": "morning", "Как мы работаем": "morning", "Лайфхак клинера": "fresh",
                   "Новостройки Тюмени": "cozy", "Акции": "cozy", "Знакомство": "morning"}


def tts_text(text: str) -> str:
    """Числа с пробелами-разделителями («13 700») синтезатор читает как два числа — склеиваем."""
    return re.sub(r"(?<=\d)[   ](?=\d{3}\b)", "", text)


def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def synthesize(text: str, speed: float, path: str):
    key = os.environ["YANDEX_SPEECHKIT_API_KEY"]
    params = {"text": tts_text(text), "lang": "ru-RU", "voice": os.environ.get("SPEECHKIT_VOICE", "alena"),
              "emotion": os.environ.get("SPEECHKIT_EMOTION", "good"), "speed": f"{speed:.2f}", "format": "oggopus"}
    if os.environ.get("YANDEX_FOLDER_ID"):
        params["folderId"] = os.environ["YANDEX_FOLDER_ID"]
    req = urllib.request.Request(TTS_URL, data=urllib.parse.urlencode(params).encode(),
                                 headers={"Authorization": f"Api-Key {key}"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
        f.write(resp.read())


def voice_for(clip, video_len: float) -> tuple[str, float]:
    """Голос клипа (кэшируется в audio/voice). Возвращает (путь, длина)."""
    os.makedirs(VOICE, exist_ok=True)
    path = os.path.join(VOICE, f"{clip['id']:02d}-{clip['slug']}.ogg")
    if not os.path.exists(path):
        synthesize(clip["voiceover"], 1.0, path)
        need = duration(path) / (video_len - VOICE_START - TAIL)
        if need > 1.0:
            synthesize(clip["voiceover"], min(MAX_SPEED, need * 1.02), path)
    return path, duration(path)


def mix(clip, with_voice: bool):
    name = f"{clip['id']:02d}-{clip['slug']}"
    src = os.path.join(SILENT, f"{name}.mp4")
    track = os.path.join(MUSIC, f"{MUSIC_BY_RUBRIC.get(clip['rubric'], 'morning')}.wav")
    video_len = duration(src)
    voice, extend = None, 0.0
    if with_voice:
        voice, vlen = voice_for(clip, video_len)
        extend = max(0.0, VOICE_START + vlen + TAIL - video_len)
    total = video_len + extend
    fade_out = max(0.0, total - 1.4)
    music_chain = f"[1:a]atrim=0:{total:.3f},afade=t=in:d=0.5,afade=t=out:st={fade_out:.3f}:d=1.4"
    if voice:
        ms = int(VOICE_START * 1000)
        graph = (f"[2:a]highpass=f=80,acompressor=threshold=0.1:ratio=3:attack=5:release=120,"
                 f"adelay={ms}|{ms},apad=whole_dur={total:.3f},asplit=2[v1][v2];"
                 f"{music_chain},volume=0.55[m];[m][v1]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=400[md];"
                 f"[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        graph = f"{music_chain},loudnorm=I=-16:TP=-1.5:LRA=11[a]"
    if extend:
        graph = f"[0:v]tpad=stop_mode=clone:stop_duration={extend:.3f}[v];" + graph
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", track]
    if voice:
        cmd += ["-i", voice]
    cmd += ["-filter_complex", graph, "-map", "[v]" if extend else "0:v", "-map", "[a]"]
    cmd += (["-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p"] if extend else ["-c:v", "copy"])
    cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.3f}", "-movflags", "+faststart",
            os.path.join(FINAL, f"{name}.mp4")]
    subprocess.run(cmd, check=True)
    return name, total, bool(voice)


def main(argv):
    music_only = "--music-only" in argv
    ids = [int(a) for a in argv if a.isdigit()]
    clips = [c for c in CLIPS if not ids or c["id"] in ids]
    unvoiced = [c for c in clips if not os.path.exists(os.path.join(VOICE, f"{c['id']:02d}-{c['slug']}.ogg"))]
    if not music_only and unvoiced and not os.environ.get("YANDEX_SPEECHKIT_API_KEY"):
        sys.exit("Нет YANDEX_SPEECHKIT_API_KEY и готового голоса для клипов "
                 f"{', '.join(str(c['id']) for c in unvoiced)} — задайте ключ или запустите с --music-only")
    if not all(os.path.exists(os.path.join(MUSIC, f"{n}.wav")) for n in music.TRACKS):
        music.build()
    os.makedirs(FINAL, exist_ok=True)
    for clip in clips:
        if not os.path.exists(os.path.join(SILENT, f"{clip['id']:02d}-{clip['slug']}.mp4")):
            print(f"{clip['id']:02d}: нет немого исходника — сначала render_clips.js")
            continue
        name, total, voiced = mix(clip, not music_only)
        print(f"{name}.mp4 — {total:.1f} с, {'голос + музыка' if voiced else 'музыка'}")


if __name__ == "__main__":
    main(sys.argv[1:])
