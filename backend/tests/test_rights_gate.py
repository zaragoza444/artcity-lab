from app.core.enums import DatasetStatus, RightsStatus
from app.services.rights_gate import assert_dataset_trainable


class FakeDS:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeDB:
    def __init__(self, dataset=None, rights=None):
        self.dataset = dataset
        self.rights = rights

    def get(self, model, id_):
        return self.dataset

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.rights


def test_trainable_ok():
    ds = FakeDS(
        id="d1",
        status=DatasetStatus.TRAINING_READY.value,
        ai_training_permission=True,
    )
    rights = FakeDS(
        ai_training=True,
        legal_status=RightsStatus.APPROVED_FOR_TRAINING.value,
    )
    out = assert_dataset_trainable(FakeDB(ds, rights), "d1")  # type: ignore[arg-type]
    assert out is ds


def test_trainable_blocked_without_rights():
    from fastapi import HTTPException

    ds = FakeDS(
        id="d1",
        status=DatasetStatus.TRAINING_READY.value,
        ai_training_permission=True,
    )
    try:
        assert_dataset_trainable(FakeDB(ds, None), "d1")  # type: ignore[arg-type]
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400
