import dspy  # type: ignore
from typing import List, Optional, Union
from personal_graph.graph import Graph
from personal_graph.models import Node


class Retriever(dspy.Retrieve):
    def __init__(
        self,
        db_url: str,
        auth_token: str,
        k: int = 5,
    ):
        super().__init__(k=k)
        self.k = k
        self.db_url = db_url
        self.auth_token = auth_token
        self.graph = Graph(db_url, auth_token)

    def _retrieve_passages(self, queries: List[str]) -> List[Node]:
        passages = []
        for query in queries:
            kg = self.graph.search_query(query)
            self.graph.visualize_graph(kg)
            passages.extend(kg.nodes)
        return passages

    def forward(
        self, query_or_queries: Union[str, List[str]], k: Optional[int] = None, **kwargs
    ) -> list[Node]:
        if not isinstance(query_or_queries, list):
            query_or_queries = [query_or_queries]
        passages = self._retrieve_passages(query_or_queries)
        return passages
