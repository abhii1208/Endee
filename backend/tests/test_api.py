from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app


@patch("backend.app.api.routes_search.search_support_knowledge")
def test_search_success(mock_search):
    from backend.app.models.domain import SearchResultItem, SupportItemType

    mock_search.return_value = [
        SearchResultItem(
            id="TCK-1001",
            type=SupportItemType.TICKET,
            title="Test ticket",
            snippet="Snippet",
            product="billing-api",
            severity="P1",
            score=0.9,
            url=None,
            resolved=None,
        )
    ]

    client = TestClient(app)
    resp = client.post(
        "/search",
        json={"query": "504 errors", "top_k": 3, "generate_answer": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "504 errors"
    assert len(data["tickets"]) == 1
    assert data["tickets"][0]["id"] == "TCK-1001"
    assert data["tickets"][0]["score"] == 0.9


@patch("backend.app.api.routes_health.get_endee_client")
def test_health_when_endee_unavailable(mock_get_client):
    mock_client = MagicMock()
    mock_client.describe_index.side_effect = Exception("connection refused")
    mock_get_client.return_value = mock_client

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("endee_status") == "unavailable"
    assert data.get("endee_index_stats") == {}
