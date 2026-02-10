from typing import List, Dict, Any, Optional

from endee import Endee, Precision
from loguru import logger

from backend.app.config import get_settings
from backend.app.models.domain import SupportItem
from backend.app.services.embeddings import get_embedding_model


class EndeeClientWrapper:
    """
    Thin wrapper around the Endee Python SDK that:
    - ensures the index exists on startup
    - exposes helper methods for upsert and query
    """

    def __init__(self) -> None:
        settings = get_settings()
        auth_token = settings.endee_auth_token or None

        self._client = Endee(auth_token) if auth_token else Endee()
        self._client.set_base_url(str(settings.endee_base_url))

        self.index_name = settings.endee_index_name
        self._index = None

        self._ensure_index()

    def _ensure_index(self) -> None:
        """
        Ensure the primary support_knowledge index exists in Endee.
        """

        settings = get_settings()
        model_dim = self._infer_embedding_dimension()

        logger.info(
            f"Ensuring Endee index '{self.index_name}' exists "
            f"(dimension={model_dim}, space_type='cosine')."
        )

        existing = [idx["name"] for idx in self._client.list_indexes()]
        if self.index_name not in existing:
            self._client.create_index(
                name=self.index_name,
                dimension=model_dim,
                space_type="cosine",
                precision=Precision.INT8D,
            )
            logger.info(f"Created Endee index '{self.index_name}'.")
        else:
            logger.info(f"Endee index '{self.index_name}' already exists.")

        self._index = self._client.get_index(self.index_name)

    def _infer_embedding_dimension(self) -> int:
        """
        Infer embedding dimension by creating a small dummy vector.

        We avoid importing the embedding model here to keep concerns
        separated; in a more advanced setup we might share this value
        via configuration.
        """

        model = get_embedding_model()
        sample_vector = model.encode("dimension-probe", convert_to_numpy=True)
        return int(sample_vector.shape[0])

    def describe_index(self) -> dict:
        return self._index.describe()

    def upsert_support_items(self, items: List[SupportItem], vectors: List[List[float]]):
        """
        Upsert a batch of support items into Endee.
        """

        if not items:
            return

        if len(items) != len(vectors):
            raise ValueError("Number of items and vectors must match.")

        to_upsert: List[Dict[str, Any]] = []
        for item, vector in zip(items, vectors):
            to_upsert.append(
                {
                    "id": item.id,
                    "vector": vector,
                    "meta": item.meta(),
                    "filter": item.filter(),
                }
            )

        logger.info(f"Upserting {len(to_upsert)} items into Endee index '{self.index_name}'.")
        self._index.upsert(to_upsert)

    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[List[Dict[str, Any]]] = None,
        ef: int = 128,
    ) -> List[Dict[str, Any]]:
        """
        Query the Endee index for nearest neighbours.
        """

        kwargs: Dict[str, Any] = {
            "vector": vector,
            "top_k": top_k,
            "ef": ef,
        }
        if filters:
            kwargs["filter"] = filters

        results = self._index.query(**kwargs)
        return results


_endee_wrapper: Optional[EndeeClientWrapper] = None


def get_endee_client() -> EndeeClientWrapper:
    """
    Lazily construct and return a singleton Endee client wrapper.
    """

    global _endee_wrapper
    if _endee_wrapper is None:
        _endee_wrapper = EndeeClientWrapper()
    return _endee_wrapper

