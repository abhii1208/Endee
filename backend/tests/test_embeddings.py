import numpy as np

from backend.app.services import embeddings


def test_embed_text_uses_model(monkeypatch):
    class DummyModel:
        def encode(self, text, convert_to_numpy=True):
            return np.array([0.1, 0.2, 0.3], dtype=np.float32)

    monkeypatch.setattr(embeddings, "get_embedding_model", lambda: DummyModel())

    vec = embeddings.embed_text("hello world")
    assert isinstance(vec, list)
    assert len(vec) == 3

