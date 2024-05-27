from vlite import VLite  # type: ignore

from personal_graph.persistence_layer.vector_store.vector_store import (
    VectorStore as VectorStore,
)
from typing import Any, Dict, List

class VliteVSS(VectorStore):
    collection: str
    model_name: str
    def __init__(
        self,
        *,
        collection: str = "./vectors",
        model_name: str = "mixedbread-ai/mxbai-embed-large-v1",
    ) -> None: ...
    vlite: VLite
    def initialize(self): ...
    def __eq__(self, other): ...
    def save(self) -> None: ...
    def add_node_embedding(self, id: Any, label: str, attribute: Dict): ...
    def add_edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict
    ) -> None: ...
    def add_edge_embeddings(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Dict[str, str]],
    ): ...
    def delete_node_embedding(self, ids: Any) -> None: ...
    def delete_edge_embedding(self, ids: Any) -> None: ...
    def vector_search_node(
        self,
        data: Dict,
        *,
        threshold: float | None = None,
        descending: bool,
        limit: int,
        sort_by: str,
    ): ...
    def vector_search_edge(
        self,
        data: Dict,
        *,
        threshold: float | None = None,
        descending: bool,
        limit: int,
        sort_by: str,
    ): ...
    def vector_search_node_from_multi_db(
        self, data: Dict, *, threshold: float | None = None, limit: int = 1
    ): ...
    def vector_search_edge_from_multi_db(
        self, data: Dict, *, threshold: float | None = None, limit: int = 1
    ): ...
