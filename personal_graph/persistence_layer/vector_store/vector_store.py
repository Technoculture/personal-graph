"""
Provide access to different vector databases
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union


class VectorStore(ABC):
    @abstractmethod
    def initialize(self):
        """Initialize the vector store."""
        pass

    @abstractmethod
    def save(self):
        """Save the embeddings into the vector store"""
        pass

    @abstractmethod
    def add_node_embedding(self, id: Any, label: str, attribute: Dict):
        """Add a single node embedding to the database."""
        pass

    @abstractmethod
    def add_edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict
    ) -> None:
        """Add a single edge embedding to the database."""
        pass

    @abstractmethod
    def add_edge_embeddings(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Union[Dict[str, str]]],
    ):
        """Add edges embeddings to the vector store"""
        pass

    @abstractmethod
    def delete_node_embedding(self, id: Any) -> None:
        """Remove a single node embedding from the database."""
        pass

    @abstractmethod
    def delete_edge_embedding(self, ids: Any) -> None:
        """Remove multiple nodes embedding from the database."""
        pass

    @abstractmethod
    def vector_search_node(
        self,
        data: Dict,
        *,
        threshold: float,
        descending: bool,
        limit: int,
        sort_by: str,
    ):
        """Perform a vector search for nodes."""
        pass

    @abstractmethod
    def vector_search_edge(
        self,
        data: Dict,
        *,
        threshold: float,
        descending: bool,
        limit: int,
        sort_by: str,
    ):
        """Perform a vector search for edges."""
        pass

    @abstractmethod
    def vector_search_node_from_multi_db(
        self, data: Dict, *, threshold: float, limit: int
    ):
        """Perform a vector search for nodes across multiple databases"""
        pass

    @abstractmethod
    def vector_search_edge_from_multi_db(
        self, data: Dict, *, threshold: float, limit: int
    ):
        """Perform a vector search for edges across multiple databases"""
        pass
