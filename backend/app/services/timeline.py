"""Cinema finishing timeline — shot list, mix levels, order for review."""

from __future__ import annotations

from typing import Any


DEFAULT_TRACKS = (
    ("picture", "Picture / cutdowns"),
    ("music", "Music bed"),
    ("voice", "Voice-over"),
    ("end", "End card"),
)


def build_timeline(
    *,
    duration_seconds: float,
    deliverables: list[dict[str, Any]],
    music_gain_db: float = 0.0,
    voice_gain_db: float = 0.0,
    duck_music_under_vo: bool = True,
) -> dict[str, Any]:
    clips: list[dict[str, Any]] = []
    t = 0.0
    # Picture: sequential channel cutdowns as review shots
    picture = [d for d in deliverables if d.get("modality") == "video"]
    slot = duration_seconds / max(1, len(picture)) if picture else duration_seconds
    for i, d in enumerate(picture):
        clips.append(
            {
                "id": f"pic-{i}",
                "track": "picture",
                "role": d.get("role"),
                "label": d.get("label") or d.get("role"),
                "start": round(t, 3),
                "end": round(min(duration_seconds, t + slot), 3),
                "job_id": d.get("job_id"),
                "media_url": d.get("media_url"),
                "mp4_url": d.get("mp4_url"),
                "aspect": d.get("aspect"),
            }
        )
        t += slot

    music = next((d for d in deliverables if d.get("role") == "music_master"), None)
    if music:
        clips.append(
            {
                "id": "mus-0",
                "track": "music",
                "role": "music_master",
                "label": music.get("label") or "Music",
                "start": 0.0,
                "end": duration_seconds,
                "job_id": music.get("job_id"),
                "media_url": music.get("media_url"),
                "gain_db": music_gain_db,
            }
        )

    voice = next((d for d in deliverables if d.get("role") == "voiceover"), None)
    if voice:
        clips.append(
            {
                "id": "vo-0",
                "track": "voice",
                "role": "voiceover",
                "label": voice.get("label") or "Voice-over",
                "start": 0.35,
                "end": duration_seconds,
                "job_id": voice.get("job_id"),
                "media_url": voice.get("media_url"),
                "gain_db": voice_gain_db,
                "duck_music": duck_music_under_vo,
            }
        )

    end = next((d for d in deliverables if d.get("role") == "end_card"), None)
    if end:
        clips.append(
            {
                "id": "end-0",
                "track": "end",
                "role": "end_card",
                "label": end.get("label") or "End card",
                "start": max(0.0, duration_seconds - 2.5),
                "end": duration_seconds,
                "job_id": end.get("job_id"),
                "media_url": end.get("media_url"),
            }
        )

    return {
        "product": "Art City Cinema",
        "kind": "finishing_timeline",
        "duration_seconds": duration_seconds,
        "fps": 24.0,
        "tracks": [{"id": tid, "label": label} for tid, label in DEFAULT_TRACKS],
        "clips": clips,
        "mix": {
            "music_gain_db": music_gain_db,
            "voice_gain_db": voice_gain_db,
            "duck_music_under_vo": duck_music_under_vo,
        },
        "status": "ready_for_review",
    }


def apply_timeline_mix(timeline: dict[str, Any], mix: dict[str, Any]) -> dict[str, Any]:
    out = dict(timeline)
    current = dict(out.get("mix") or {})
    if "music_gain_db" in mix:
        current["music_gain_db"] = float(mix["music_gain_db"])
    if "voice_gain_db" in mix:
        current["voice_gain_db"] = float(mix["voice_gain_db"])
    if "duck_music_under_vo" in mix:
        current["duck_music_under_vo"] = bool(mix["duck_music_under_vo"])
    out["mix"] = current
    # Mirror gains onto clips
    clips = []
    for c in out.get("clips") or []:
        item = dict(c)
        if item.get("track") == "music":
            item["gain_db"] = current.get("music_gain_db", 0.0)
            item["duck_music"] = current.get("duck_music_under_vo", True)
        if item.get("track") == "voice":
            item["gain_db"] = current.get("voice_gain_db", 0.0)
        clips.append(item)
    out["clips"] = clips
    out["status"] = "mix_updated"
    return out
