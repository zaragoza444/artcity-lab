"""Local production media factory — Cinema frames, music, VO, and MP4-ready posters."""

from __future__ import annotations

import hashlib
import io
import math
import struct
import wave
from dataclasses import dataclass
from html import escape
from uuid import uuid4


@dataclass
class MediaFile:
    filename: str
    content_type: str
    data: bytes
    kind: str  # image | audio | video_proxy | video


def _wav_bytes(samples: list[float], sample_rate: int = 22050) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for s in samples:
            val = max(-1.0, min(1.0, s))
            frames += struct.pack("<h", int(val * 32767))
        wf.writeframes(bytes(frames))
    return buf.getvalue()


def _tone(
    seconds: float,
    freq: float,
    *,
    sample_rate: int = 22050,
    volume: float = 0.35,
    attack: float = 0.02,
    release: float = 0.08,
) -> list[float]:
    n = int(seconds * sample_rate)
    out: list[float] = []
    for i in range(n):
        t = i / sample_rate
        env = 1.0
        if t < attack:
            env = t / attack
        elif t > seconds - release:
            env = max(0.0, (seconds - t) / release)
        # Soft triangle-ish with harmonics for less harsh stubs
        wave_v = (
            math.sin(2 * math.pi * freq * t)
            + 0.35 * math.sin(2 * math.pi * freq * 2 * t)
            + 0.15 * math.sin(2 * math.pi * freq * 3 * t)
        )
        out.append(wave_v * volume * env * 0.55)
    return out


def _silence(seconds: float, sample_rate: int = 22050) -> list[float]:
    return [0.0] * int(seconds * sample_rate)


def _normalize_to_lufs(samples: list[float], target_lufs: float = -16.0) -> list[float]:
    """Scale PCM floats so RMS-based LUFS estimate hits target (local QC)."""
    if not samples:
        return samples
    mean_sq = sum(s * s for s in samples) / len(samples)
    rms = math.sqrt(mean_sq) if mean_sq > 0 else 1e-9
    current = 20.0 * math.log10(rms) - 0.691
    gain = 10 ** ((target_lufs - current) / 20.0)
    out = [max(-1.0, min(1.0, s * gain)) for s in samples]
    return out


def _exact_duration(samples: list[float], seconds: float, sample_rate: int = 22050) -> list[float]:
    target = int(seconds * sample_rate)
    if len(samples) > target:
        return samples[:target]
    if len(samples) < target:
        return samples + [0.0] * (target - len(samples))
    return samples


def _hash_color(text: str) -> tuple[str, str]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    a = digest[:6]
    b = digest[6:12]
    return f"#{a}", f"#{b}"


def make_image(prompt: str, title: str = "Art City Frame") -> MediaFile:
    c1, c2 = _hash_color(prompt)
    safe_prompt = escape(prompt[:180])
    safe_title = escape(title)
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="v" cx="50%" cy="40%" r="70%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.55"/>
    </radialGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#g)"/>
  <rect width="1280" height="720" fill="url(#v)"/>
  <rect x="48" y="48" width="1184" height="624" fill="none" stroke="#efd39a" stroke-width="2" opacity="0.7"/>
  <text x="80" y="120" fill="#efd39a" font-family="Georgia, serif" font-size="28" letter-spacing="6">ART CITY</text>
  <text x="80" y="180" fill="#f3f6fa" font-family="Georgia, serif" font-size="48">{safe_title}</text>
  <foreignObject x="80" y="240" width="1120" height="360">
    <div xmlns="http://www.w3.org/1999/xhtml" style="color:#d5dbe6;font:28px Georgia,serif;line-height:1.45">
      {safe_prompt}
    </div>
  </foreignObject>
  <text x="80" y="660" fill="#8d9aad" font-family="monospace" font-size="16">LOCAL PRODUCTION PROXY · IMAGE</text>
</svg>
"""
    return MediaFile(
        filename=f"image-{uuid4().hex[:10]}.svg",
        content_type="image/svg+xml",
        data=svg.encode("utf-8"),
        kind="image",
    )


def make_video_proxy(prompt: str, duration_seconds: float = 4.0) -> tuple[MediaFile, MediaFile]:
    """Visual storyboard + audio bed acting as a local video preview pack."""
    c1, c2 = _hash_color(prompt + ":video")
    safe = escape(prompt[:160])
    frames = max(3, min(8, int(duration_seconds) + 2))
    panels = []
    for i in range(frames):
        x = 40 + i * ((1200 - 40) / frames)
        w = (1200 / frames) - 12
        panels.append(
            f'<rect x="{x:.1f}" y="260" width="{w:.1f}" height="280" fill="{c1 if i % 2 == 0 else c2}" opacity="0.85"/>'
            f'<text x="{x + 12:.1f}" y="520" fill="#0a0f16" font-family="monospace" font-size="18">SHOT {i + 1:02d}</text>'
        )
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#0a0f16"/>
  <rect x="24" y="24" width="1232" height="672" fill="none" stroke="#efd39a" stroke-width="2"/>
  <text x="56" y="90" fill="#efd39a" font-family="Georgia, serif" font-size="26" letter-spacing="8">ART CITY · VIDEO</text>
  <text x="56" y="150" fill="#f3f6fa" font-family="Georgia, serif" font-size="36">Preview Timeline</text>
  <text x="56" y="200" fill="#b7c2d1" font-family="Georgia, serif" font-size="22">{safe}</text>
  {"".join(panels)}
  <text x="56" y="660" fill="#8d9aad" font-family="monospace" font-size="16">DURATION {duration_seconds:.1f}s · 16:9 PROXY</text>
</svg>
"""
    visual = MediaFile(
        filename=f"video-{uuid4().hex[:10]}.svg",
        content_type="image/svg+xml",
        data=svg.encode("utf-8"),
        kind="video_proxy",
    )
    # Cinematic rising fifths bed
    samples: list[float] = []
    chord = [110.0, 165.0, 220.0, 330.0]
    remaining = duration_seconds
    idx = 0
    while remaining > 0:
        seg = min(0.85, remaining)
        samples += _tone(seg, chord[idx % len(chord)], volume=0.28)
        remaining -= seg
        idx += 1
    audio = MediaFile(
        filename=f"video-bed-{uuid4().hex[:10]}.wav",
        content_type="audio/wav",
        data=_wav_bytes(samples),
        kind="audio",
    )
    return visual, audio


def make_voice_conversation(prompt: str, lines: list[str] | None = None) -> MediaFile:
    """Conversation / dialogue stub — alternating speaker tones."""
    dialogue = lines if lines else [part.strip() for part in prompt.split("/") if part.strip()]
    if not dialogue:
        dialogue = [prompt[:120] or "Art City dialogue"]

    samples: list[float] = []
    # Two speakers: lower + higher formant centers
    speakers = [(180.0, 0.32), (260.0, 0.3)]
    for i, line in enumerate(dialogue[:12]):
        speaker = speakers[i % 2]
        # Length scales with text
        seconds = min(2.8, max(0.55, len(line) * 0.045))
        samples += _tone(seconds, speaker[0], volume=speaker[1])
        samples += _silence(0.18)
    return MediaFile(
        filename=f"voice-{uuid4().hex[:10]}.wav",
        content_type="audio/wav",
        data=_wav_bytes(samples),
        kind="audio",
    )


def make_music(prompt: str, duration_seconds: float = 8.0) -> MediaFile:
    scale = [196.0, 220.0, 246.94, 261.63, 293.66, 329.63, 349.23, 392.0]
    seed = int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)
    samples: list[float] = []
    t = 0.0
    step = 0
    while t < duration_seconds:
        note = scale[(seed + step) % len(scale)]
        seg = 0.4 if step % 4 else 0.7
        seg = min(seg, duration_seconds - t)
        samples += _tone(seg, note, volume=0.26)
        samples += _silence(0.05)
        t += seg + 0.05
        step += 1
    return MediaFile(
        filename=f"music-{uuid4().hex[:10]}.wav",
        content_type="audio/wav",
        data=_wav_bytes(samples),
        kind="audio",
    )


def make_sfx(prompt: str) -> MediaFile:
    # Short impact + whoosh-ish sweep
    samples: list[float] = []
    samples += _tone(0.12, 80.0, volume=0.5, attack=0.005, release=0.08)
    for i in range(18):
        freq = 600 - i * 25
        samples += _tone(0.03, freq, volume=0.18, attack=0.002, release=0.02)
    samples += _silence(0.15)
    tag = (prompt or "sfx")[:40]
    _ = tag
    return MediaFile(
        filename=f"sfx-{uuid4().hex[:10]}.wav",
        content_type="audio/wav",
        data=_wav_bytes(samples),
        kind="audio",
    )


ASPECT_SIZES = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
}


def make_cinematic_music(prompt: str, duration_seconds: float = 15.0, style: str = "epic") -> MediaFile:
    """Advertising music bed with bass + pad + melody stems mixed to -16 LUFS."""
    styles = {
        "epic": [98.0, 146.83, 196.0, 246.94, 293.66, 392.0],
        "warm": [130.81, 164.81, 196.0, 220.0, 261.63, 329.63],
        "pulse": [110.0, 110.0, 164.81, 220.0, 164.81, 330.0],
        "soft": [174.61, 196.0, 220.0, 261.63, 293.66, 349.23],
    }
    scale = styles.get(style, styles["epic"])
    seed = int(hashlib.sha256((prompt + style).encode()).hexdigest()[:8], 16)
    sample_rate = 22050
    target = int(duration_seconds * sample_rate)
    samples = [0.0] * target
    t = 0.0
    step = 0
    while t < duration_seconds:
        root = scale[(seed + step) % len(scale)]
        bass = root * 0.5
        fifth = root * 1.5
        seg = 0.5 if style == "pulse" else (0.55 if step % 3 else 0.9)
        seg = min(seg, duration_seconds - t)
        a = _tone(seg, bass, volume=0.2, sample_rate=sample_rate)
        b = _tone(seg, root, volume=0.16, sample_rate=sample_rate)
        c = _tone(seg, fifth, volume=0.1, sample_rate=sample_rate)
        start = int(t * sample_rate)
        for i, (x, y, z) in enumerate(zip(a, b, c)):
            idx = start + i
            if idx >= target:
                break
            samples[idx] += x + y + z
        if style == "pulse" and step % 2 == 0:
            hit = _tone(0.08, root * 2, volume=0.12, attack=0.005, release=0.05, sample_rate=sample_rate)
            for i, h in enumerate(hit):
                idx = start + i
                if idx < target:
                    samples[idx] += h
        t += seg + 0.03
        step += 1
    # End sting
    sting = _tone(0.45, scale[0] * 2, volume=0.18, attack=0.02, release=0.25, sample_rate=sample_rate)
    for i, s in enumerate(sting):
        idx = target - len(sting) + i
        if 0 <= idx < target:
            samples[idx] += s
    samples = _normalize_to_lufs(_exact_duration(samples, duration_seconds, sample_rate), -16.0)
    return MediaFile(
        filename="music_master.wav",
        content_type="audio/wav",
        data=_wav_bytes(samples, sample_rate=sample_rate),
        kind="audio",
    )


def _formant_syllable(seconds: float, base_hz: float, sample_rate: int = 22050) -> list[float]:
    """Lightweight formant-ish TTS proxy (owned Art City voice bed until neural TTS)."""
    n = int(seconds * sample_rate)
    out: list[float] = []
    f1, f2 = base_hz * 2.2, base_hz * 3.6
    for i in range(n):
        t = i / sample_rate
        env = 1.0
        if t < 0.02:
            env = t / 0.02
        elif t > seconds - 0.04:
            env = max(0.0, (seconds - t) / 0.04)
        vibrato = 1.0 + 0.012 * math.sin(2 * math.pi * 5.2 * t)
        v = (
            0.55 * math.sin(2 * math.pi * base_hz * vibrato * t)
            + 0.28 * math.sin(2 * math.pi * f1 * t)
            + 0.12 * math.sin(2 * math.pi * f2 * t)
        )
        out.append(v * 0.38 * env)
    return out


def make_ad_voiceover(script: str, brand: str = "Art City", dialect: str | None = None) -> MediaFile:
    """Broadcast-style VO with syllable timing; dialect shifts base pitch slightly."""
    lines = [ln.strip() for ln in script.replace(".", ".\n").split("\n") if ln.strip()]
    if not lines:
        lines = [f"{brand} — craft the story."]
    dialect_shift = {"sorani": 0.0, "badini": 8.0, "kurmanji": -6.0}.get((dialect or "").lower(), 0.0)
    samples: list[float] = []
    samples += _silence(0.25)
    for i, line in enumerate(lines[:14]):
        words = max(1, len(line.split()))
        for w, word in enumerate(line.split()[:24]):
            sec = min(0.55, max(0.12, len(word) * 0.045))
            base = (168.0 if i % 2 == 0 else 188.0) + dialect_shift + (w % 3) * 3
            samples += _formant_syllable(sec, base)
            samples += _silence(0.04)
        samples += _silence(0.16)
        _ = words
    samples += _tone(0.32, 250.0 + dialect_shift, volume=0.18, attack=0.02, release=0.18)
    samples = _normalize_to_lufs(samples, -16.0)
    return MediaFile(
        filename="voiceover.wav",
        content_type="audio/wav",
        data=_wav_bytes(samples),
        kind="audio",
    )


def make_cinema_poster_png(
    *,
    campaign: str,
    brief: str,
    cta: str,
    brand: str = "Art City",
    aspect: str = "16:9",
    filename: str = "poster.png",
) -> MediaFile:
    """Raster poster for ffmpeg MP4 mux (PIL)."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = ASPECT_SIZES.get(aspect, ASPECT_SIZES["16:9"])
    c1, c2 = _hash_color(campaign + aspect + brief[:40])
    img = Image.new("RGB", (width, height), "#05070b")
    draw = ImageDraw.Draw(img)
    # Gradient-ish bands
    for y in range(height):
        t = y / max(1, height - 1)
        # blend ink → accent
        def hex_rgb(h: str) -> tuple[int, int, int]:
            h = h.lstrip("#")
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        r1, g1, b1 = hex_rgb("#05070b")
        r2, g2, b2 = hex_rgb(c2)
        r = int(r1 * (1 - t) + r2 * t * 0.55)
        g = int(g1 * (1 - t) + g2 * t * 0.55)
        b = int(b1 * (1 - t) + b2 * t * 0.55)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    margin = int(min(width, height) * 0.06)
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline="#efd39a",
        width=max(2, width // 640),
    )
    try:
        font_lg = ImageFont.truetype("DejaVuSans.ttf", size=max(28, width // 28))
        font_md = ImageFont.truetype("DejaVuSans.ttf", size=max(20, width // 40))
        font_sm = ImageFont.truetype("DejaVuSans.ttf", size=max(16, width // 52))
    except OSError:
        font_lg = ImageFont.load_default()
        font_md = font_lg
        font_sm = font_lg
    draw.text((margin + 24, margin + 28), "ART CITY · CINEMA", fill="#efd39a", font=font_sm)
    draw.text((margin + 24, margin + 80), campaign[:48], fill="#f3f6fa", font=font_lg)
    draw.text((margin + 24, margin + 150), brief[:90], fill="#b7c2d1", font=font_md)
    draw.text((margin + 24, height - margin - 90), cta[:40], fill="#c5a15e", font=font_md)
    draw.text(
        (margin + 24, height - margin - 48),
        f"{brand} · {aspect} · MP4 MASTER",
        fill="#8d9aad",
        font=font_sm,
    )
    # Shot markers
    shots = 5
    for i in range(shots):
        x0 = margin + 24 + i * ((width - 2 * margin - 48) // shots)
        w = (width - 2 * margin - 48) // shots - 12
        y0 = height // 2 - 40
        fill = c1 if i % 2 == 0 else c2
        draw.rectangle([x0, y0, x0 + w, y0 + 120], fill=fill)
        draw.text((x0 + 10, y0 + 48), f"SHOT {i + 1:02d}", fill="#0a0f16", font=font_sm)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return MediaFile(
        filename=filename,
        content_type="image/png",
        data=buf.getvalue(),
        kind="image",
    )


def make_cinematic_video(
    prompt: str,
    *,
    aspect: str = "16:9",
    duration_seconds: float = 15.0,
    brand: str = "Art City",
    campaign: str = "Campaign",
    cta: str = "Watch now",
) -> tuple[MediaFile, MediaFile]:
    """Cinematic advertising storyboard proxy with music/VO bed."""
    width, height = ASPECT_SIZES.get(aspect, ASPECT_SIZES["16:9"])
    c1, c2 = _hash_color(prompt + aspect + campaign)
    safe_prompt = escape(prompt[:140])
    safe_campaign = escape(campaign[:48])
    safe_brand = escape(brand[:32])
    safe_cta = escape(cta[:28])
    shots = [
        ("OPEN", "Atmospheric establish"),
        ("HOOK", "Emotion / product beat"),
        ("STORY", "Human moment"),
        ("BRAND", f"{safe_brand} lockup"),
        ("CTA", safe_cta),
    ]
    # Layout differs for portrait vs landscape
    portrait = height > width
    panels = []
    if portrait:
        for i, (label, caption) in enumerate(shots):
            y = 160 + i * ((height - 280) / len(shots))
            h = ((height - 280) / len(shots)) - 16
            fill = c1 if i % 2 == 0 else c2
            panels.append(
                f'<rect x="48" y="{y:.1f}" width="{width - 96}" height="{h:.1f}" fill="{fill}" opacity="0.88"/>'
                f'<text x="72" y="{y + 36:.1f}" fill="#0a0f16" font-family="Georgia, serif" font-size="28">{label}</text>'
                f'<text x="72" y="{y + 68:.1f}" fill="#0a0f16" font-family="Georgia, serif" font-size="18">{escape(caption)}</text>'
            )
    else:
        for i, (label, caption) in enumerate(shots):
            x = 48 + i * ((width - 80) / len(shots))
            w = ((width - 80) / len(shots)) - 14
            fill = c1 if i % 2 == 0 else c2
            panels.append(
                f'<rect x="{x:.1f}" y="{height * 0.38:.1f}" width="{w:.1f}" height="{height * 0.38:.1f}" fill="{fill}" opacity="0.88"/>'
                f'<text x="{x + 16:.1f}" y="{height * 0.38 + 42:.1f}" fill="#0a0f16" font-family="Georgia, serif" font-size="24">{label}</text>'
                f'<text x="{x + 16:.1f}" y="{height * 0.38 + 72:.1f}" fill="#0a0f16" font-family="Georgia, serif" font-size="16">{escape(caption)}</text>'
            )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#05070b"/>
      <stop offset="55%" stop-color="#101824"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <rect x="20" y="20" width="{width - 40}" height="{height - 40}" fill="none" stroke="#efd39a" stroke-width="2" opacity="0.75"/>
  <text x="48" y="70" fill="#efd39a" font-family="Georgia, serif" font-size="22" letter-spacing="7">ART CITY · CINEMA</text>
  <text x="48" y="118" fill="#f3f6fa" font-family="Georgia, serif" font-size="40">{safe_campaign}</text>
  <text x="48" y="160" fill="#b7c2d1" font-family="Georgia, serif" font-size="20">{safe_prompt}</text>
  {"".join(panels)}
  <text x="48" y="{height - 36}" fill="#8d9aad" font-family="monospace" font-size="15">{aspect} · {duration_seconds:.0f}s · ADVERTISING MASTER PROXY</text>
</svg>
"""
    role_name = {"16:9": "broadcast_hero", "9:16": "social_vertical", "1:1": "social_square"}.get(
        aspect, "cinema_video"
    )
    visual = MediaFile(
        filename=f"{role_name}.svg",
        content_type="image/svg+xml",
        data=svg.encode("utf-8"),
        kind="video_proxy",
    )
    # Continuous bed of exact spot length (sync gate)
    bed_samples: list[float] = []
    chord = [98.0, 147.0, 196.0, 294.0]
    filled = 0.0
    idx = 0
    while filled < duration_seconds:
        seg = min(0.75, duration_seconds - filled)
        root = chord[idx % len(chord)]
        a = _tone(seg, root, volume=0.2)
        b = _tone(seg, root * 1.5, volume=0.1)
        bed_samples += [x + y for x, y in zip(a, b)]
        filled += seg
        idx += 1
    bed_samples = _normalize_to_lufs(_exact_duration(bed_samples, duration_seconds), -16.0)
    audio = MediaFile(
        filename=f"{role_name}_audio_bed.wav",
        content_type="audio/wav",
        data=_wav_bytes(bed_samples),
        kind="audio",
    )
    return visual, audio


def make_end_card(campaign: str, cta: str, brand: str = "Art City", prompt: str = "") -> MediaFile:
    """End card at broadcast 16:9 export resolution with Art City brand colours."""
    # Official Art City cinema palette (matches product UI)
    gold = "#c5a15e"
    gold_bright = "#efd39a"
    ink = "#05070b"
    paper = "#f3f6fa"
    mist = "#8d9aad"
    width, height = 1920, 1080
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="{ink}"/>
  <rect x="96" y="96" width="{width - 192}" height="{height - 192}" fill="none" stroke="{gold_bright}" stroke-width="3"/>
  <rect x="120" y="120" width="72" height="72" fill="none" stroke="{gold}" stroke-width="2"/>
  <text x="156" y="168" text-anchor="middle" fill="{gold_bright}" font-family="Georgia, serif" font-size="22" font-weight="700">AC</text>
  <text x="{width // 2}" y="380" text-anchor="middle" fill="{gold_bright}" font-family="Georgia, serif" font-size="34" letter-spacing="12">{escape(brand.upper())}</text>
  <text x="{width // 2}" y="480" text-anchor="middle" fill="{paper}" font-family="Georgia, serif" font-size="64">{escape(campaign[:48])}</text>
  <text x="{width // 2}" y="560" text-anchor="middle" fill="{paper}" font-family="Georgia, serif" font-size="32">{escape(cta[:56])}</text>
  <text x="{width // 2}" y="640" text-anchor="middle" fill="{mist}" font-family="Georgia, serif" font-size="22">{escape(prompt[:90])}</text>
  <text x="{width // 2}" y="980" text-anchor="middle" fill="{mist}" font-family="monospace" font-size="16">16:9 · 1920x1080 · ART CITY END CARD</text>
</svg>
"""
    return MediaFile(
        filename="end_card.svg",
        content_type="image/svg+xml",
        data=svg.encode("utf-8"),
        kind="image",
    )


def make_brand_logo() -> MediaFile:
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="#05070b"/>
  <rect x="48" y="48" width="416" height="416" fill="none" stroke="#efd39a" stroke-width="8"/>
  <text x="256" y="290" text-anchor="middle" fill="#efd39a" font-family="Georgia, serif" font-size="120" font-weight="700">AC</text>
  <text x="256" y="360" text-anchor="middle" fill="#c5a15e" font-family="Georgia, serif" font-size="28" letter-spacing="10">ART CITY</text>
</svg>
"""
    return MediaFile(
        filename="art_city_logo.svg",
        content_type="image/svg+xml",
        data=svg.encode("utf-8"),
        kind="image",
    )
