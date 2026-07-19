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
            ("Kardokh", "sorani", "Art City boy character — Story Bible hero of homecoming.", "character"),
            ("Kurdiya", "sorani", "Art City girl character — Story Bible companion of homecoming.", "character"),
            ("Newroz", "sorani", "Kurdish New Year / spring celebration.", "customs"),
            ("Zagros", "sorani", "Mountain range central to Kurdish geography.", "geography"),
        ]
        for term, dialect, definition, category in knowledge:
            if db.query(KnowledgeEntry).filter(KnowledgeEntry.term == term).first():
                continue
            db.add(
                KnowledgeEntry(
                    id=str(uuid4()),
                    term=term,
                    language="ku",
                    dialect=dialect,
                    definition=definition,
                    child_friendly_definition=definition,
                    category=category,
                    source="Art City Story Bible",
                    licence="Art City proprietary",
                    approval_status="approved",
                    created_by=admin.id,
                )
            )

        db.commit()
        print("AI Core seed complete")
        print(f"  datasets: {kd.name}, {ku.name}")
        print(f"  models: {mk.name}, {mu.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
