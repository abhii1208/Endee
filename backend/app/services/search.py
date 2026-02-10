from typing import List, Dict, Any

from backend.app.models.domain import (
    SearchResultItem,
    SupportItemType,
)
from backend.app.models.schemas import SearchRequest
from backend.app.services.embeddings import embed_text
from backend.app.services.endee_client import get_endee_client


def _build_filter_clauses(request: SearchRequest) -> List[Dict[str, Any]]:
    """
    Translate high-level SearchFilters into Endee filter clauses.
    """

    if not request.filters:
        return []

    filters: List[Dict[str, Any]] = []
    f = request.filters

    if f.product:
        filters.append({"product": {"$eq": f.product}})
    if f.severity:
        filters.append({"severity": {"$eq": f.severity}})
    if f.types:
        filters.append({"type": {"$in": f.types}})

    return filters


def search_support_knowledge(request: SearchRequest) -> List[SearchResultItem]:
    """
    Execute a semantic search over support knowledge stored in Endee.
    """

    query_vector = embed_text(request.query)
    filters = _build_filter_clauses(request)

    top_k = min(request.top_k + 5, 50)

    client = get_endee_client()
    raw_results = client.query(
        vector=query_vector,
        top_k=top_k,
        filters=filters if filters else None,
        ef=128,
    )

    results: List[SearchResultItem] = []
    for item in raw_results:
        meta = item.get("meta", {}) or {}
        support_type = SupportItemType(meta.get("type", "ticket"))
        title = meta.get("title") or meta.get("question") or "Untitled"
        snippet = meta.get("snippet") or ""

        results.append(
            SearchResultItem(
                id=item["id"],
                type=support_type,
                title=title,
                snippet=snippet,
                product=meta.get("product"),
                severity=meta.get("severity"),
                score=float(item.get("similarity", 0.0)),
                url=meta.get("url"),
            )
        )

    return results

