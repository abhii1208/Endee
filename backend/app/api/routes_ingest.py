from typing import List

from fastapi import APIRouter, HTTPException

from backend.app.config import get_settings
from backend.app.models.domain import SupportItem, SupportItemType
from backend.app.models.schemas import IngestItemRequest
from backend.app.services.embeddings import embed_texts
from backend.app.services.endee_client import get_endee_client

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", status_code=201)
async def ingest_items(items: List[IngestItemRequest]) -> dict:
    settings = get_settings()
    if len(items) > settings.max_ingest_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum of {settings.max_ingest_batch_size}. Split into smaller batches.",
        )

    domain_items: List[SupportItem] = []
    texts: List[str] = []

    for payload in items:
        item = SupportItem(
            id=payload.id,
            type=SupportItemType(payload.type),
            title=payload.title,
            body=payload.body,
            product=payload.product,
            severity=payload.severity,
            tags=payload.tags,
            url=payload.url,
            resolved=payload.resolved,
            priority=payload.priority,
        )
        domain_items.append(item)
        texts.append(item.to_text())

    vectors = embed_texts(texts)
    client = get_endee_client()
    client.upsert_support_items(domain_items, vectors)

    return {"ingested": len(domain_items)}

