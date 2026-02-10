from typing import List

from backend.app.models.domain import SupportItem, SupportItemType
from backend.app.services.endee_client import EndeeClientWrapper


class DummyIndex:
    def __init__(self):
        self.upserted = []

    def upsert(self, items: List[dict]):
        self.upserted.extend(items)

    def describe(self):
        return {"num_vectors": len(self.upserted)}


class DummyEndee:
    def __init__(self):
        self._indexes = {}

    def set_base_url(self, url: str):
        self.base_url = url

    def list_indexes(self):
        return [{"name": name} for name in self._indexes.keys()]

    def create_index(self, name, dimension, space_type, precision):
        self._indexes[name] = DummyIndex()

    def get_index(self, name):
        return self._indexes[name]


def test_upsert_support_items(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.endee_client.Endee", lambda *args, **kwargs: DummyEndee()
    )

    wrapper = EndeeClientWrapper()
    index = wrapper._index

    items = [
        SupportItem(
            id="T1",
            type=SupportItemType.TICKET,
            title="Test ticket",
            body="Something is broken",
        )
    ]
    vectors = [[0.1, 0.2, 0.3, 0.4]]

    wrapper.upsert_support_items(items, vectors)

    assert len(index.upserted) == 1
    assert index.upserted[0]["id"] == "T1"

