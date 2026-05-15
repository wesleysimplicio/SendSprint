"""Generate lightweight local music bed and sound effects for Remotion videos."""

from __future__ import annotations

import math
import wave
from pathlib import Path

SAMPLE_RATE = 22_050
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "audio"


def clamp(value: float) -> int:
    return max(-32767, min(32767, int(value * 32767)))


def envelope(t: float, duration: float, attack: float = 0.02, release: float = 0.12) -> float:
    if t < attack:
        return t / attack
    if t > duration - release:
        return max(0.0, (duration - t) / release)
    return 1.0


def write_mono(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = (
            clamp(sample).to_bytes(2, "little", signed=True)
            for sample in samples
        )
        wav.writeframes(b"".join(frames))


def tone(
    freq: float,
    duration: float,
    *,
    volume: float = 0.32,
    bend: float = 0.0,
    harmonic: float = 0.25,
) -> list[float]:
    total = int(SAMPLE_RATE * duration)
    data: list[float] = []
    phase = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        f = freq + bend * (t / duration)
        phase += 2 * math.pi * f / SAMPLE_RATE
        amp = envelope(t, duration)
        sample = math.sin(phase) + harmonic * math.sin(phase * 2.01)
        data.append(sample * volume * amp)
    return data


def chord(freqs: tuple[float, ...], duration: float, *, volume: float = 0.22) -> list[float]:
    total = int(SAMPLE_RATE * duration)
    data: list[float] = []
    for i in range(total):
        t = i / SAMPLE_RATE
        amp = envelope(t, duration, attack=0.04, release=0.2)
        sample = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        data.append(sample * volume * amp)
    return data


def background(duration: float = 62.0) -> list[float]:
    total = int(SAMPLE_RATE * duration)
    progression = [
        (110.0, 164.81, 220.0, 329.63),
        (98.0, 146.83, 196.0, 293.66),
        (130.81, 196.0, 261.63, 392.0),
        (87.31, 130.81, 174.61, 261.63),
    ]
    data: list[float] = []
    for i in range(total):
        t = i / SAMPLE_RATE
        bar = int(t // 3.0) % len(progression)
        freqs = progression[bar]
        pad = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        pulse = 0.55 + 0.45 * max(0.0, math.sin(2 * math.pi * 2 * t))
        bass = math.sin(2 * math.pi * freqs[0] * 0.5 * t)
        shimmer = math.sin(2 * math.pi * (freqs[2] * 2) * t) * 0.12
        fade = min(1.0, t / 3.0, (duration - t) / 3.0)
        data.append((pad * 0.16 + bass * 0.08 * pulse + shimmer * 0.05) * fade)
    return data


def click() -> list[float]:
    return tone(880, 0.12, volume=0.22, bend=180, harmonic=0.1)


def whoosh() -> list[float]:
    return tone(220, 0.34, volume=0.26, bend=880, harmonic=0.35)


def error() -> list[float]:
    first = tone(180, 0.2, volume=0.34, bend=-40, harmonic=0.45)
    gap = [0.0] * int(SAMPLE_RATE * 0.04)
    second = tone(140, 0.24, volume=0.34, bend=-55, harmonic=0.45)
    return first + gap + second


def success() -> list[float]:
    return chord((523.25, 659.25, 783.99), 0.42, volume=0.28)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_mono(OUT / "sendsprint-bed.wav", background())
    write_mono(OUT / "sendsprint-click.wav", click())
    write_mono(OUT / "sendsprint-whoosh.wav", whoosh())
    write_mono(OUT / "sendsprint-error.wav", error())
    write_mono(OUT / "sendsprint-success.wav", success())


if __name__ == "__main__":
    build()
