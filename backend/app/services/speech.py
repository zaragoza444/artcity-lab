"""Kurdish speech / ASR preparation (Sprint 4 scaffolding)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    dialect: Optional[str] = None
    confidence: float = 0.0


def simulate_asr(audio_key: str, dialect: str = "sorani") -> list[TranscriptSegment]:
    """Placeholder ASR until Art City speech worker is attached."""
    return [
        TranscriptSegment(
            start=0.0,
            end=2.5,
            text="[Art City ASR pilot — attach Kurdish model]",
            speaker="speaker_1",
            dialect=dialect,
            confidence=0.0,
        )
    ]


def build_transcript_manifest(segments: list[TranscriptSegment]) -> dict:
    return {
        "engine": "artcity-asr-pilot",
        "status": "scaffold",
        "segments": [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text,
                "speaker": s.speaker,
                "dialect": s.dialect,
                "confidence": s.confidence,
            }
            for s in segments
        ],
    }
