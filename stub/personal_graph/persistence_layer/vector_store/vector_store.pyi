import abc
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class VectorStore(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def initialize(self): ...
    @abstractmethod
    def save(self): ...
    @abstractmethod
    def add_node_embedding(self, id: Any, label: str, attribute: Dict): ...
    @abstractmethod
    def add_edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict
    ) -> None: ...
    @abstractmethod
    def add_edge_embeddings(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Dict[str, str]],
    ): ...
    @abstractmethod
    def delete_node_embedding(self, id: Any) -> None: ...
    @abstractmethod
    def delete_edge_embedding(self, ids: Any) -> None: ...
    @abstractmethod
    def vector_search_node(
        self,
        data: Dict,
        *,
        threshold: float,
        descending: bool,
        limit: int,
        sort_by: str,
    ): ...
    @abstractmethod
    def vector_search_edge(
        self,
        data: Dict,
        *,
        threshold: float,
        descending: bool,
        limit: int,
        sort_by: str,
    ): ...
    @abstractmethod
    def vector_search_node_from_multi_db(
        self, data: Dict, *, threshold: float, limit: int
    ): ...
    @abstractmethod
    def vector_search_edge_from_multi_db(
        self, data: Dict, *, threshold: float, limit: int
    ): ...
