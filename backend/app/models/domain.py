from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any


class SupportItemType(str, Enum):
    TICKET = "ticket"
    FAQ = "faq"
    RUNBOOK = "runbook"


@dataclass
class SupportItem:
    """
    Internal representation of a support knowledge item that will be stored
    in Endee as a vector with metadata and filter fields.
    """

    id: str
    type: SupportItemType
    title: str
    body: str
    product: Optional[str] = None
    severity: Optional[str] = None
    tags: Optional[List[str]] = None
    url: Optional[str] = None

    def to_text(self) -> str:
        """
        Canonical text representation used for embedding.
        """

        lines = [self.title.strip(), "", self.body.strip()]
        return "\n".join([line for line in lines if line])

    def meta(self) -> Dict[str, Any]:
        """
        Metadata stored in Endee; used for display and optional prompting.
        """

        return {
            "type": self.type.value,
            "title": self.title,
            "product": self.product,
            "severity": self.severity,
            "tags": self.tags or [],
            "url": self.url,
        }

    def filter(self) -> Dict[str, Any]:
        """
        Filter fields used in Endee queries.
        """

        filt: Dict[str, Any] = {}
        if self.product:
            filt["product"] = self.product
        if self.severity:
            filt["severity"] = self.severity
        if self.type:
            filt["type"] = self.type.value
        return filt


@dataclass
class SearchResultItem:
    """
    Normalised search result returned to the API layer.
    """

    id: str
    type: SupportItemType
    title: str
    snippet: str
    product: Optional[str]
    severity: Optional[str]
    score: float
    url: Optional[str] = None

