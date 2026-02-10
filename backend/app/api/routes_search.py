from fastapi import APIRouter

from backend.app.models.schemas import SearchRequest, SearchResponse, SearchResultItemSchema
from backend.app.services.answer import generate_answer, is_llm_enabled
from backend.app.services.search import search_support_knowledge

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_support(request: SearchRequest) -> SearchResponse:
    """
    Main semantic search endpoint.
    """

    results = search_support_knowledge(request)

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
        tickets=tickets[: request.top_k],
        faqs=faqs[: request.top_k],
        runbooks=runbooks[: request.top_k],
        llm_answer=llm_answer,
    )

