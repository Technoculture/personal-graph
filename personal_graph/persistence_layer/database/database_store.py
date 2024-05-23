from abc import ABC, abstractmethod

import libsql_experimental as libsql  # type: ignore
from typing import Any, Callable, Dict, Optional, List, Union
from graphviz import Digraph  # type: ignore

from personal_graph.models import Node, Edge

CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


class DatabaseStore(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def fetch_node_embed_id(self, node_id: Any):
        pass

    @abstractmethod
    def fetch_edge_embed_ids(self, id: Any):
        pass

    @abstractmethod
    def all_connected_nodes(self, node_or_edge: Union[Node | Edge]) -> Any:
        pass

    @abstractmethod
    def get_connections(self, identifier: Any) -> CursorExecFunction:
        pass

    @abstractmethod
    def search_edge(self, source: Any, target: Any, attributes: Dict):
        pass

    @abstractmethod
    def add_node(self, label: str, attribute: Dict, id: Any):
        pass

    @abstractmethod
    def add_edge(self, source: Any, target: Any, label: str, attributes: Dict) -> None:
        pass

    @abstractmethod
    def update_node(self, node: Node):
        pass

    @abstractmethod
    def remove_node(self, id: Any) -> None:
        pass

    @abstractmethod
    def search_node(self, node_id: Any) -> Any:
        pass

    @abstractmethod
    def search_node_label(self, node_id: Any) -> Any:
        pass

    @abstractmethod
    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        pass

    @abstractmethod
    def fetch_node_id(self, id: Any):
        pass

    @abstractmethod
    def find_nodes_by_label(self, label: str):
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
        pass

    @abstractmethod
    def fetch_ids_from_db(self) -> List[str]:
        pass

    @abstractmethod
    def search_indegree_edges(self, target: Any) -> List[Any]:
        pass

    @abstractmethod
    def search_outdegree_edges(self, source: Any) -> List[Any]:
        pass

    @abstractmethod
    def search_similar_nodes(
        self, embed_id, *, desc: Optional[bool] = False, sort_by: Optional[str] = ""
    ):
        pass

    @abstractmethod
    def search_similar_edges(
        self, embed_id, *, desc: Optional[bool] = False, sort_by: Optional[str] = ""
    ):
        pass
