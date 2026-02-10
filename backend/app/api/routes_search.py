import time

from fastapi import APIRouter, HTTPException

from loguru import logger

from backend.app.config import get_settings
from backend.app.models.schemas import SearchRequest, SearchResponse, SearchResultItemSchema
from backend.app.services.answer import generate_answer, is_llm_enabled
from backend.app.services.search import search_support_knowledge

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_support(request: SearchRequest) -> SearchResponse:
    settings = get_settings()
    top_k = min(request.top_k, settings.max_top_k)
    copy_fn = getattr(request, "model_copy", request.copy)
    request_capped = copy_fn(update={"top_k": top_k})
    filters_repr = None
    if request.filters:
        filters_repr = getattr(request.filters, "model_dump", request.filters.dict)()
    start = time.perf_counter()
    try:
        results = search_support_knowledge(request_capped)
    except Exception as exc:
        logger.exception("Search failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Search failed. The vector database may be unavailable. Check backend logs.",
        ) from exc
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "search query_len=%s top_k=%s filters=%s latency_ms=%.1f",
        len(request.query),
        top_k,
        filters_repr,
        elapsed_ms,
    )

    tickets = []
    faqs = []
    runbooks = []

    for item in results:
        schema = SearchResultItemSchema(
            id=item.id,
            type=item.type.value,
            title=item.title,
            snippet=item.snippet,
            product=item.product,
            severity=item.severity,
            score=item.score,
            url=item.url,
            resolved=getattr(item, "resolved", None),
        )
        if item.type.value == "ticket":
            tickets.append(schema)
        elif item.type.value == "faq":
            faqs.append(schema)
        elif item.type.value == "runbook":
            runbooks.append(schema)

    llm_answer = None
    if request.generate_answer and is_llm_enabled():
        llm_answer = generate_answer(request.query, results)

    return SearchResponse(
        query=request.query,
        tickets=tickets[:top_k],
        faqs=faqs[:top_k],
        runbooks=runbooks[:top_k],
        llm_answer=llm_answer,
    )

