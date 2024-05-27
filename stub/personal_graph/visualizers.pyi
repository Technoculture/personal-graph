from graphviz import Digraph  # type: ignore
from personal_graph.models import KnowledgeGraph as KnowledgeGraph
from typing import Any, List, Tuple

def graphviz_visualize_bodies(
    dot_file: str,
    path: List[Tuple[Any, str, str]] = [],
    format: str = "png",
    exclude_node_keys: List[str] = [],
    hide_node_key: bool = False,
    node_kv: str = " ",
    exclude_edge_keys: List[str] = [],
    hide_edge_key: bool = False,
    edge_kv: str = " ",
) -> None: ...
def visualize_graph(kg: KnowledgeGraph) -> Digraph: ...
