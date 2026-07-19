from app.services.router_engine import resolve_route


class EmptyDB:
    def query(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return None

    def get(self, *args, **kwargs):
        return None


def test_default_image_route():
    decision = resolve_route(EmptyDB(), modality="image")  # type: ignore[arg-type]
    assert decision.provider == "artcity-image"


def test_default_video_route():
    decision = resolve_route(EmptyDB(), modality="video")  # type: ignore[arg-type]
    assert decision.provider == "artcity-video"
