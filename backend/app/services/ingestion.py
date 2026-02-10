import csv
import json
from pathlib import Path
from typing import List

from loguru import logger

from backend.app.models.domain import SupportItem, SupportItemType
from backend.app.services.embeddings import embed_texts
from backend.app.services.endee_client import get_endee_client


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"


def load_tickets(path: Path) -> List[SupportItem]:
    items: List[SupportItem] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            resolved = None
            if row.get("resolved", "").strip().lower() in ("true", "1", "yes"):
                resolved = True
            elif row.get("resolved", "").strip().lower() in ("false", "0", "no"):
                resolved = False
            try:
                priority = int(row["priority"]) if row.get("priority") else None
            except (ValueError, KeyError):
                priority = None
            if priority is not None and (priority < 0 or priority > 999):
                priority = None
            items.append(
                SupportItem(
                    id=row["id"],
                    type=SupportItemType.TICKET,
                    title=row["title"],
                    body=row["description"],
                    product=row.get("product") or None,
                    severity=row.get("severity") or None,
                    tags=[t.strip() for t in (row.get("tags") or "").split(",") if t.strip()],
                    url=row.get("url") or None,
                    resolved=resolved,
                    priority=priority,
                )
            )
    return items


def load_faqs(path: Path) -> List[SupportItem]:
    items: List[SupportItem] = []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        p = entry.get("priority")
        priority = int(p) if p is not None else None
        if priority is not None and (priority < 0 or priority > 999):
            priority = None
        items.append(
            SupportItem(
                id=entry["id"],
                type=SupportItemType.FAQ,
                title=entry["question"],
                body=entry["answer"],
                product=entry.get("product"),
                severity=None,
                tags=entry.get("tags") or [],
                url=entry.get("url"),
                priority=priority,
            )
        )
    return items


def load_runbooks(path: Path) -> List[SupportItem]:
    items: List[SupportItem] = []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        steps = "\n".join(entry.get("steps", []))
        p = entry.get("priority")
        priority = int(p) if p is not None else None
        if priority is not None and (priority < 0 or priority > 999):
            priority = None
        items.append(
            SupportItem(
                id=entry["id"],
                type=SupportItemType.RUNBOOK,
                title=entry["title"],
                body=steps,
                product=entry.get("product"),
                severity=entry.get("severity"),
                tags=entry.get("tags") or [],
                url=entry.get("url"),
                priority=priority,
            )
        )
    return items


def ingest_all() -> None:
    """
    Ingest all sample data files from the data/ directory into Endee.
    """

    tickets_file = DATA_DIR / "tickets.csv"
    faqs_file = DATA_DIR / "faqs.json"
    runbooks_file = DATA_DIR / "runbooks.json"

    items: List[SupportItem] = []

    if tickets_file.exists():
        logger.info(f"Loading tickets from {tickets_file}")
        items.extend(load_tickets(tickets_file))
    if faqs_file.exists():
        logger.info(f"Loading FAQs from {faqs_file}")
        items.extend(load_faqs(faqs_file))
    if runbooks_file.exists():
        logger.info(f"Loading runbooks from {runbooks_file}")
        items.extend(load_runbooks(runbooks_file))

    if not items:
        logger.warning("No data found to ingest. Ensure CSV/JSON files exist in data/.")
        return

    texts = [item.to_text() for item in items]
    vectors = embed_texts(texts)

    client = get_endee_client()
    client.upsert_support_items(items, vectors)

    logger.info(f"Ingested {len(items)} support items into Endee.")


if __name__ == "__main__":
    ingest_all()

