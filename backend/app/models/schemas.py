from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    product: Optional[str] = Field(
        default=None, description="Filter results by product identifier"
    )
    severity: Optional[str] = Field(
        default=None,
        description="Filter results by severity (e.g. P0/P1/P2 or high/medium/low)",
    )
    types: Optional[List[Literal["ticket", "faq", "runbook"]]] = Field(
        default=None, description="Restrict result types"
    )
    priority_min: Optional[int] = Field(
        default=None, ge=0, le=999, description="Min priority (Endee $range filter)"
    )
    priority_max: Optional[int] = Field(
        default=None, ge=0, le=999, description="Max priority (Endee $range filter)"
    )


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language description of the issue")
    top_k: int = Field(
        10,
        ge=1,
        le=50,
        description="Number of results per content type to return",
    )
    filters: Optional[SearchFilters] = None
    generate_answer: bool = Field(
        True,
        description="Whether to attempt LLM-based answer generation if configured",
    )


class SearchResultItemSchema(BaseModel):
    id: str
    type: str
    title: str
    snippet: str
    product: Optional[str] = None
    severity: Optional[str] = None
    score: float
    url: Optional[str] = None
    resolved: Optional[bool] = None


class SearchResponse(BaseModel):
    query: str
    tickets: List[SearchResultItemSchema]
    faqs: List[SearchResultItemSchema]
    runbooks: List[SearchResultItemSchema]
    llm_answer: Optional[str] = None


class IngestItemRequest(BaseModel):
    """
    Schema for ingesting a single support item via the API.
    Useful for demos or incremental updates.
    """

    id: str
    type: Literal["ticket", "faq", "runbook"]
    title: str
    body: str
    product: Optional[str] = None
    severity: Optional[str] = None
    tags: Optional[List[str]] = None
    url: Optional[str] = None
    resolved: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=999)

