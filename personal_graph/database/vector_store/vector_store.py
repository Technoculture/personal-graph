"""
Provide access to different vector databases
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union, Optional


class VectorStore(ABC):
    @abstractmethod
    def initialize(self):
        """Initialize the database."""
        pass

    @abstractmethod
    def save(self):
        """Save the data into the database"""
        pass

    @abstractmethod
    def add_node_embedding(self, id: Any, attribute: Dict):
        """Add a single node to the database."""
        pass

    @abstractmethod
    def add_edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict
    ) -> None:
        """Add a single edge to the database."""
        pass

    @abstractmethod
    def add_edge_embeddings(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Union[Dict[str, str]]],
    ):
        pass

    @abstractmethod
    def delete_node_embedding(self, id: Any) -> None:
        """Remove a single node from the database."""
        pass

    @abstractmethod
    def delete_edge_embedding(self, ids: Any) -> None:
        """Remove multiple nodes from the database."""
        pass

    @abstractmethod
    def vector_search_node(
        self,
        data: Dict,
        *,
        threshold: Optional[float] = None,
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
        threshold: Optional[float] = None,
        descending: bool,
        limit: int,
        sort_by: str,
    ):
        """Perform a vector search for edges."""
        pass