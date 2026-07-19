"""Seed admin user, Kardokh/Kurdiya pilot datasets, models, routes, knowledge."""

from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.enums import DatasetStatus, ModelStatus, RightsStatus
from app.core.security import hash_password
from app.models import Dataset, KnowledgeEntry, RegisteredModel, RightsRecord, RouteRule, User


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.default_admin_email).first()
        if not admin:
            admin = User(
                id=str(uuid4()),
                email=settings.default_admin_email,
                full_name="Art City Admin",
                password_hash=hash_password(settings.default_admin_password),
                role="super_admin",
            )
            db.add(admin)
            db.flush()
            print(f"Created admin {admin.email}")
        else:
            print(f"Admin exists {admin.email}")

        def ensure_dataset(name: str, character: str) -> Dataset:
            ds = db.query(Dataset).filter(Dataset.name == name).first()
            if ds:
                return ds
            ds = Dataset(
                id=str(uuid4()),
                name=name,
                description=f"Verified character reference dataset for {character}",
                category="character_references",
                media_type="image",
                language="ku",
                dialect="sorani",
                owner="Art City",
                copyright_holder="Art City Group",
                licence="Art City proprietary",
                commercial_use=True,
                ai_training_permission=True,
                version="v2",
                status=DatasetStatus.TRAINING_READY.value,
                checksum=sha256(name.encode()).hexdigest(),
                intended_model_use=f"AC-{character.upper()}-IMAGE",
                record_count=24,
                created_by=admin.id,
            )
            db.add(ds)
            db.flush()
            rights = RightsRecord(
                id=str(uuid4()),
                dataset_id=ds.id,
                copyright_owner="Art City Group",
                source_organisation="Art City",
                commercial_use=True,
                ai_training=True,
                fine_tuning=True,
                image_generation=True,
                legal_status=RightsStatus.APPROVED_FOR_TRAINING.value,
                legal_notes="Pilot seed — Art City owned character IP",
                created_by=admin.id,
            )
            db.add(rights)
            return ds

        kd = ensure_dataset("KD-CHARACTER-001-v2", "kardokh")
        ku = ensure_dataset("KD-CHARACTER-002-v2", "kurdiya")

        def ensure_model(name: str, dataset: Dataset, character: str) -> RegisteredModel:
            m = db.query(RegisteredModel).filter(RegisteredModel.name == name).first()
            if m:
                return m
            checksum = sha256(f"{name}:{dataset.id}".encode()).hexdigest()
            m = RegisteredModel(
                id=str(uuid4()),
                name=name,
                version="v1",
                model_type="lora",
                base_model="Approved image base model",
                licence="Art City proprietary",
                commercial_use=True,
                owner="Art City",
                training_dataset_id=dataset.id,
                training_method="lora",
                character_key=character,
                modality="image",
                status=ModelStatus.STAGING.value,
                checkpoint_path=f"models/{name}/checkpoint.safetensors",
                checksum=checksum,
                quality_score=0.86,
                created_by=admin.id,
            )
            db.add(m)
            db.flush()
            return m

        mk = ensure_model("AC-KARDOKH-IMAGE-v1", kd, "kardokh")
        mu = ensure_model("AC-KURDIYA-IMAGE-v1", ku, "kurdiya")

        for name, modality, character, model, provider, priority in [
            ("Kardokh image", "image", "kardokh", mk, "artcity-image", 10),
            ("Kurdiya image", "image", "kurdiya", mu, "artcity-image", 10),
            ("Default image", "image", None, None, "artcity-image", 100),
            ("Default video", "video", None, None, "artcity-video", 100),
            ("Default voice", "voice", None, None, "artcity-voice", 100),
            ("Default music", "music", None, None, "artcity-music", 100),
            ("Default audio", "audio", None, None, "artcity-audio", 100),
            ("Advertising video", "video", None, None, "artcity-video", 20),
        ]:
            exists = (
                db.query(RouteRule)
                .filter(RouteRule.name == name)
                .first()
            )
            if exists:
                continue
            db.add(
                RouteRule(
                    id=str(uuid4()),
                    name=name,
                    modality=modality,
                    character_key=character,
                    model_id=model.id if model else None,
                    provider=provider,
                    priority=priority,
                    is_active=True,
                )
            )

        knowledge = [
            ("Kardokh", "sorani", "Art City boy character — Story Bible hero of homecoming.", "character", "Kardokh", "کاردۆخ گەڕایەوە بۆ ماڵ."),
            ("Kurdiya", "sorani", "Art City girl character — Story Bible companion of homecoming.", "character", "Kurdiya", "کوردیا چیرۆک دەگێڕێتەوە."),
            ("Newroz", "sorani", "Kurdish New Year / spring celebration.", "customs", "Newroz", "نەورۆز جەژنی بەهارە."),
            ("Zagros", "sorani", "Mountain range central to Kurdish geography.", "geography", "Zagros", "زاگرۆس شاخی نیشتمانە."),
            ("Kardokh", "badini", "Art City boy character — Badini Story Bible naming.", "character", "Kardokh", "کاردۆخ ڤەگەڕیا بۆ مال."),
            ("Kurdiya", "badini", "Art City girl character — Badini Story Bible naming.", "character", "Kurdiya", "کوردیا چیرۆکێ دبێژیت."),
            ("Newroz", "kurmanji", "Kurdish New Year celebrated across the mountains.", "customs", "Newroz", "Newroz cejna biharê ye."),
            ("Zagros", "kurmanji", "Mountain range of Kurdish homeland geography.", "geography", "Zagros", "Zagros çiyayên welat in."),
            ("Shayi", "sorani", "Kurdish folk dance / celebration movement.", "customs", "Shayi", "شایی جووڵەی خۆشی و کۆمەڵایەتییە."),
            ("Sorani", "sorani", "Central Kurdish dialect used across Art City scripts.", "terminology", "Central Kurdish", None),
            ("Badini", "badini", "Northern Iraq Kurdish dialect (Behdini).", "terminology", "Badini", None),
            ("Kurmanji", "kurmanji", "Northern Kurdish dialect (Latin script).", "terminology", "Kurmanji", None),
        ]
        for term, dialect, definition, category, translation, example in knowledge:
            exists = (
                db.query(KnowledgeEntry)
                .filter(KnowledgeEntry.term == term, KnowledgeEntry.dialect == dialect)
                .first()
            )
            if exists:
                continue
            db.add(
                KnowledgeEntry(
                    id=str(uuid4()),
                    term=term,
                    language="ku",
                    dialect=dialect,
                    definition=definition,
                    child_friendly_definition=definition,
                    translation=translation,
                    example_sentence=example,
                    category=category,
                    source="Art City Story Bible",
                    licence="Art City proprietary",
                    approval_status="approved",
                    created_by=admin.id,
                )
            )

        speech_ds = db.query(Dataset).filter(Dataset.name == "KD-SPEECH-KU-v1").first()
        if not speech_ds:
            speech_ds = Dataset(
                id=str(uuid4()),
                name="KD-SPEECH-KU-v1",
                description="Kurdish speech corpus scaffold — Sorani / Badini / Kurmanji",
                category="speech",
                media_type="audio",
                language="ku",
                dialect="sorani",
                owner="Art City",
                copyright_holder="Art City Group",
                licence="Art City proprietary",
                commercial_use=True,
                ai_training_permission=True,
                version="v1",
                status=DatasetStatus.EVALUATION_ONLY.value,
                checksum=sha256(b"KD-SPEECH-KU-v1").hexdigest(),
                intended_model_use="AC-KURDISH-ASR",
                record_count=0,
                created_by=admin.id,
            )
            db.add(speech_ds)
            db.flush()
            db.add(
                RightsRecord(
                    id=str(uuid4()),
                    dataset_id=speech_ds.id,
                    copyright_owner="Art City Group",
                    source_organisation="Art City",
                    commercial_use=True,
                    ai_training=True,
                    fine_tuning=True,
                    image_generation=False,
                    legal_status=RightsStatus.APPROVED_FOR_TRAINING.value,
                    legal_notes="Speech pilot seed — Art City owned",
                    created_by=admin.id,
                )
            )

        asr_model = db.query(RegisteredModel).filter(RegisteredModel.name == "AC-KURDISH-ASR-v1").first()
        if not asr_model:
            asr_model = RegisteredModel(
                id=str(uuid4()),
                name="AC-KURDISH-ASR-v1",
                version="v1",
                model_type="asr",
                base_model="Art City speech base",
                licence="Art City proprietary",
                commercial_use=True,
                owner="Art City",
                training_dataset_id=speech_ds.id,
                training_method="supervised",
                character_key=None,
                modality="speech",
                status=ModelStatus.EVALUATING.value,
                checkpoint_path="models/AC-KURDISH-ASR-v1/pilot",
                checksum=sha256(b"AC-KURDISH-ASR-v1").hexdigest(),
                quality_score=0.72,
                created_by=admin.id,
            )
            db.add(asr_model)
            db.flush()

        asr_route = db.query(RouteRule).filter(RouteRule.name == "Kurdish ASR").first()
        if not asr_route:
            db.add(
                RouteRule(
                    id=str(uuid4()),
                    name="Kurdish ASR",
                    modality="speech",
                    character_key=None,
                    model_id=asr_model.id,
                    provider="artcity-asr",
                    priority=10,
                    is_active=True,
                )
            )
        elif asr_route.provider != "artcity-asr":
            asr_route.provider = "artcity-asr"
            asr_route.model_id = asr_model.id
            asr_route.is_active = True
            db.add(asr_route)

        db.commit()
        print("AI Core seed complete")
        print(f"  datasets: {kd.name}, {ku.name}, {speech_ds.name}")
        print(f"  models: {mk.name}, {mu.name}, {asr_model.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
