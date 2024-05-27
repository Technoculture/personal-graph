import dspy  # type: ignore
from personal_graph.graph import GraphDB as GraphDB, Node as Node
from typing import List

class PersonalRM(dspy.Retrieve):
    k: int
    graph: GraphDB
    def __init__(self, graph: GraphDB, k: int = 5) -> None: ...
    def forward(
        self, query_or_queries: str | List[str], k: int | None = None, **kwargs
    ) -> List[dspy.Prediction]: ...
