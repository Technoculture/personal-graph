"""
Provide access to different vector databases
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from personal_graph.models import Node, Edge


class BaseVectorStore(ABC):
    @abstractmethod
    def initialize(self):
        """Initialize the database."""
        pass

    @abstractmethod
    def add_node(self, label: str, attribute: Dict, id: Any):
        """Add a single node to the database."""
        pass

    @abstractmethod
    def add_nodes(
        self, attributes: List[Union[Dict[str, str]]], labels: List[str], ids: List[Any]
    ) -> None:
        """Add multiple nodes to the database."""
        pass

    @abstractmethod
    def add_edge(self, source: Any, target: Any, label: str, attributes: Dict) -> None:
        """Add a single edge to the database."""
        pass

    @abstractmethod
    def add_edges(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Union[Dict[str, str]]],
    ):
        """Add multiple edges to the database."""
        pass

    @abstractmethod
    def update_node(self, node: Node):
        """Update a node in the database."""
        pass

    @abstractmethod
    def remove_node(self, id: Any) -> None:
        """Remove a single node from the database."""
        pass

    @abstractmethod
    def remove_nodes(self, ids: List[Any]) -> None:
        """Remove multiple nodes from the database."""
        pass

    @abstractmethod
    def search_node(self, node_id: Any) -> Any:
        """Search for a node by its ID."""
        pass

    @abstractmethod
    def search_node_label(self, node_id: Any) -> Any:
        """Search for a node's label by its ID."""
        pass

    @abstractmethod
    def vector_search_node(
        self, data: Dict, *, descending: bool, limit: int, sort_by: str
    ):
        """Perform a vector search for nodes."""
        pass

    @abstractmethod
    def vector_search_edge(
        self, data: Dict, *, descending: bool, limit: int, sort_by: str
    ):
        """Perform a vector search for edges."""
        pass

    @abstractmethod
    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        """Traverse the graph from a source node to a target node."""
        pass

    @abstractmethod
    def merge_by_similarity(self, threshold) -> None:
        """Merge similar nodes based on a similarity threshold."""
        pass

    @abstractmethod
    def find_nodes_like(self, label: str, threshold: float) -> List[Node]:
        """Find nodes with a label similar to the given label."""
        pass

    @abstractmethod
    def fetch_ids_from_db(self) -> List[str]:
        """Fetch all node IDs from the database."""
        pass

    @abstractmethod
    def search_indegree_edges(self, target: Any) -> List[Any]:
        """Search for incoming edges to a target node."""
        pass

    @abstractmethod
    def search_outdegree_edges(self, source: Any) -> List[Any]:
        """Search for outgoing edges from a source node."""
        pass

    @abstractmethod
    def get_connections(self, id: Any):
        pass

    @abstractmethod
    def all_connected_nodes(self, node_or_edge: Union[Node | Edge]):
        """Get all connected nodes"""
        pass
