"""Enrich generation prompts with approved Kurdish Knowledge Base entries."""

from __future__ import annotations

import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models import KnowledgeEntry

_TOKEN_RE = re.compile(r"[A-Za-z\u0600-\u06FF]{3,}")


def enrich_prompt(
    db: Session,
    prompt: str,
    *,
    character_key: Optional[str] = None,
    dialect: Optional[str] = None,
    limit: int = 4,
) -> tuple[str, list[dict]]:
    """
    Append concise cultural notes from approved KB hits.
    Returns (enriched_prompt, hit_summaries).
    """
    text = (prompt or "").strip()
    if not text:
        return text, []

    candidates: list[str] = []
    if character_key:
        candidates.append(character_key)
        if character_key == "kardokh":
            candidates.append("Kardokh")
        elif character_key == "kurdiya":
            candidates.append("Kurdiya")
    candidates.extend(_TOKEN_RE.findall(text))

    # Prefer longer / proper names first
    seen: set[str] = set()
    ordered: list[str] = []
    for c in candidates:
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(c)

    hits: list[KnowledgeEntry] = []
    for term in ordered:
        q = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.approval_status == "approved",
            KnowledgeEntry.term.ilike(term),
        )
        if dialect:
            q = q.filter(KnowledgeEntry.dialect == dialect)
        hit = q.first()
        if hit and hit.id not in {h.id for h in hits}:
            hits.append(hit)
        if len(hits) >= limit:
            break

    if not hits:
        # Fallback: any approved character/geography terms mentioned loosely
        loose = (
            db.query(KnowledgeEntry)
            .filter(KnowledgeEntry.approval_status == "approved")
            .order_by(KnowledgeEntry.term.asc())
            .limit(40)
            .all()
        )
        lower = text.lower()
        for entry in loose:
            if entry.term.lower() in lower and entry.id not in {h.id for h in hits}:
                hits.append(entry)
            if len(hits) >= limit:
                break

    if not hits:
        return text, []

    notes = "; ".join(f"{h.term}: {h.definition}" for h in hits)
    enriched = f"{text}\n\n[Art City cultural context — {dialect or 'ku'}] {notes}"
    summary = [
        {
            "id": h.id,
            "term": h.term,
            "dialect": h.dialect,
            "category": h.category,
            "definition": h.definition,
        }
        for h in hits
    ]
    return enriched, summary
