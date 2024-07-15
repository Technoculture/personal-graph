from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, List, Union
from graphviz import Digraph  # type: ignore

from personal_graph.models import Node, Edge

# CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]
CursorExecFunction = Callable[[Any, Any], Any]  # TODO: Constraint the type


class DB(ABC):
    """
    Abstract Base Class (ABC) for a graph database interface.

    This class defines methods for implementing a graph database with various
    operations such as adding, updating, removing nodes and edges, traversing the
    graph, and visualizing it. Implementations of this class should provide concrete
    behavior for each of the abstract methods.
    """

    @abstractmethod
    def initialize(self):
        """Initialize the database"""
        pass

    @abstractmethod
    def __eq__(self, other):
        """Check equality with another DB object"""
        pass

    @abstractmethod
    def save(self):
        """Save the current state of the database"""
        pass

    @abstractmethod
    def fetch_node_embed_id(self, node_id: Any):
        """Fetch the embedding ID of a node given its ID"""
        pass

    @abstractmethod
    def fetch_edge_embed_ids(self, id: Any):
        """Fetch the embedding IDs of edges given a node or edge ID"""
        pass

    @abstractmethod
    def all_connected_nodes(self, node_or_edge: Union[Node | Edge]) -> Any:
        """Retrieve all nodes connected to a given node or edge"""
        pass

    @abstractmethod
    def get_connections(self, identifier: Any) -> CursorExecFunction:
        """Get connections for a given identifier."""
        pass

    @abstractmethod
    def search_edge(self, source: Any, target: Any, attributes: Dict):
        """Search for an edge given its source, target, and attributes"""
        pass

    @abstractmethod
    def add_node(self, label: str, attribute: Dict, id: Any):
        """Add a node to the database"""
        pass

    @abstractmethod
    def add_edge(self, source: Any, target: Any, label: str, attributes: Dict) -> None:
        """Add an edge to the database"""
        pass

    @abstractmethod
    def update_node(self, node: Node):
        """Update a node in the database"""
        pass

    @abstractmethod
    def remove_node(self, id: Any) -> None:
        """Remove a node from the database"""
        pass

    @abstractmethod
    def search_node(self, node_id: Any) -> Any:
        """Search for a node by its ID"""
        pass

    @abstractmethod
    def search_node_label(self, node_id: Any) -> Any:
        """Search for a node label by its ID"""
        pass

    @abstractmethod
    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        """Traverse the graph from a source to an optional target node"""
        pass

    @abstractmethod
    def fetch_node_id(self, id: Any):
        """Fetch a node ID given another identifier"""
        pass

    @abstractmethod
    def find_nodes_by_label(self, label: str):
        """Find nodes by their label"""
        pass

    @abstractmethod
    def graphviz_visualize(
        self,
        dot_file: Optional[str] = None,
        path: List[Any] = [],
        connections: Any = None,
        format: str = "png",
        exclude_node_keys: List[str] = [],
        hide_node_key: bool = False,
        node_kv: str = " ",
        exclude_edge_keys: List[str] = [],
        hide_edge_key: bool = False,
        edge_kv: str = " ",
    ) -> Digraph:
        """Visualize the graph using Graphviz"""
        pass

    @abstractmethod
    def fetch_ids_from_db(self) -> List[str]:
        """Fetch all IDs from the database"""
        pass

    @abstractmethod
    def search_indegree_edges(self, target: Any) -> List[Any]:
        """Search for edges with the given target node"""
        pass

    @abstractmethod
    def search_outdegree_edges(self, source: Any) -> List[Any]:
        """Search for edges with the given source node"""
        pass

    @abstractmethod
    def search_similar_nodes(self, embed_id, *, desc: bool, sort_by: str):
        """Search for nodes similar to the given embedding ID"""
        pass

    @abstractmethod
    def search_similar_edges(self, embed_id, *, desc: bool, sort_by: str):
        """Search for edges similar to the given embedding ID"""
        pass
