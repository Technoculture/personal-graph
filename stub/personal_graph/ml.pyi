import networkx as nx  # type: ignore
from personal_graph import (
    Edge as Edge,
    EdgeInput as EdgeInput,
    GraphDB as GraphDB,
    KnowledgeGraph as KnowledgeGraph,
    Node as Node,
)

def pg_to_networkx(graph: GraphDB, *, post_visualize: bool = False): ...
def networkx_to_pg(
    networkx_graph: nx,
    graph: GraphDB,
    *,
    post_visualize: bool = False,
    override: bool = True,
): ...
