"""Нежная фоновая музыка для клипов, синтезированная с нуля (без чужих сэмплов и прав).

Три трека в разных тональностях: мягкий пэд, «войлочное» фортепиано арпеджио, тихий бас, реверберация.
    python3 marketing/tools/music.py      → marketing/audio/music/{morning,fresh,cozy}.wav (48 кГц, стерео, 64 с)
"""

from __future__ import annotations

import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "audio", "music"))
RNG = np.random.default_rng(72)

# (название, bpm, аккорды: (бас MIDI, верхние ноты MIDI), шаблон арпеджио, колокольчики)
TRACKS = {
    "morning": (72, [(41, [57, 60, 65, 69]), (40, [55, 60, 64, 67]), (38, [57, 62, 65, 69]), (34, [58, 62, 65, 70])],
                [0, 1, 2, 3, 2, 1, 2, 3], False),
    "fresh": (84, [(43, [59, 62, 67, 71]), (38, [57, 62, 66, 69]), (40, [59, 64, 67, 71]), (36, [60, 64, 67, 72])],
              [0, 2, 1, 3, 2, 3, 1, 2], True),
    "cozy": (64, [(38, [57, 61, 62, 66]), (35, [57, 59, 62, 66]), (43, [59, 62, 66, 67]), (45, [57, 61, 64, 66])],
             [0, 1, 2, 3, 1, 2, 3, 2], False),
}


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    return sosfilt(butter(2, cutoff, btype="low", fs=SR, output="sos"), x, axis=0)


def adsr(n: int, a: float, r: float) -> np.ndarray:
    env = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    env[:na] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    env[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    return env


def pad_note(midi: int, dur: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for ch, cents in ((0, -6), (1, 6)):
        f = hz(midi) * 2 ** (cents / 1200)
        w = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
        out[:, ch] = w * (0.85 + 0.15 * np.sin(2 * np.pi * 0.2 * t + ch))
    return out * adsr(n, 1.4, 1.8)[:, None]


def piano_note(midi: int, vel: float, length: float = 3.2) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    w = np.zeros(n)
    for k, (amp, dec) in enumerate(((1.0, 2.2), (0.42, 3.4), (0.2, 4.8), (0.08, 6.5), (0.035, 8.0)), start=1):
        w += amp * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-dec * t)
    w *= 1 - np.exp(-t / 0.006)
    return lowpass(w * vel, 2600)


def bell(midi: int, vel: float) -> np.ndarray:
    n = int(4.0 * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    w = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-3 * t)) * np.exp(-1.2 * t)
    return w * (1 - np.exp(-t / 0.003)) * vel


def place(buf: np.ndarray, sig: np.ndarray, start: float, pan: float = 0.0):
    i = int(max(0.0, start) * SR)
    if i >= len(buf):
        return
    if sig.ndim == 1:
        angle = (pan + 1) * np.pi / 4  # равномощная панорама: pan от −1 (лево) до 1 (право)
        sig = np.stack([sig * np.cos(angle), sig * np.sin(angle)], axis=1)
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def reverb(x: np.ndarray, seconds: float = 2.6, wet: float = 0.3) -> np.ndarray:
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = RNG.standard_normal((n, 2)) * np.exp(-t / (seconds / 5.5))[:, None]
    ir = lowpass(ir, 5500)
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    out = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return (1 - wet) * x + wet * out


def track(bpm: int, chords, arp, bells: bool, seconds: float = 64.0) -> np.ndarray:
    beat = 60 / bpm
    bar = 4 * beat
    total = int((seconds + 4) * SR)
    pad = np.zeros((total, 2))
    keys = np.zeros((total, 2))
    bass = np.zeros((total, 2))
    t, i = 0.0, 0
    while t < seconds:
        root, upper = chords[i % len(chords)]
        for m in upper[:3]:
            place(pad, pad_note(m, bar + 1.6) * 0.1, t)
        place(bass, piano_note(root + 12, 0.35, 4.0), t, 0.0)
        for s, idx in enumerate(arp):
            vel = 0.22 + 0.05 * RNG.random() - (0.04 if s % 2 else 0)
            place(keys, piano_note(upper[idx] + 12, vel), t + s * beat / 2 + RNG.normal(0, 0.006), pan=(idx - 1.5) * 0.25)
        if bells and i % 2 == 1:
            place(keys, bell(upper[-1] + 24, 0.06), t + 2 * beat, pan=0.4)
        t += bar
        i += 1
    mix = lowpass(pad, 2200) + keys + lowpass(bass, 500) * 0.7
    mix = sosfilt(butter(2, 70, btype="high", fs=SR, output="sos"), mix, axis=0)  # без гула на телефонах
    mix = reverb(mix)[: int(seconds * SR)]
    mix *= adsr(len(mix), 1.5, 3.0)[:, None]
    return mix / np.max(np.abs(mix)) * 0.89


def build():
    os.makedirs(OUT, exist_ok=True)
    for name, (bpm, chords, arp, bells) in TRACKS.items():
        audio = track(bpm, chords, arp, bells)
        wavfile.write(os.path.join(OUT, f"{name}.wav"), SR, (audio * 32767).astype(np.int16))
        print(f"{name}.wav — {len(audio) / SR:.0f} с, {bpm} bpm")


if __name__ == "__main__":
    build()
