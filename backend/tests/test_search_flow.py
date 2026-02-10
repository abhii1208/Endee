from typing import List

from backend.app.models.domain import SearchResultItem, SupportItemType
from backend.app.models.schemas import SearchRequest
from backend.app.services import search as search_service


class DummyClient:
    def __init__(self, results: List[dict]):
        self._results = results

    def query(self, vector, top_k=10, filters=None, ef=128):
        return self._results


def test_search_support_knowledge_basic(monkeypatch):
    monkeypatch.setattr(
        search_service, "embed_text", lambda text: [0.1, 0.2, 0.3]
    )

    dummy_results = [
        {
            "id": "TCK-1001",
            "similarity": 0.92,
            "meta": {
                "type": "ticket",
                "title": "Intermittent 504s on payments API",
                "snippet": "504 Gateway Timeout on /v1/payments for EU customers.",
                "product": "billing-api",
                "severity": "P1",
            },
        }
    ]

    monkeypatch.setattr(
        search_service, "get_endee_client", lambda: DummyClient(dummy_results)
    )

    request = SearchRequest(query="504 errors on payments", top_k=5, filters=None)
    results: List[SearchResultItem] = search_service.search_support_knowledge(request)

    assert len(results) == 1
    item = results[0]
    assert item.id == "TCK-1001"
    assert item.type == SupportItemType.TICKET
    assert item.product == "billing-api"
    assert item.severity == "P1"

