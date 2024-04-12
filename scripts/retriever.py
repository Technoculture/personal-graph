import os
import sys
import dspy  # type: ignore
from typing import List, Optional, Union

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from personal_graph.graph import Graph
from personal_graph.models import Node
from dotenv import load_dotenv

load_dotenv()


class Retriever(dspy.Retrieve):
    def __init__(
        self,
        db_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        k: int = 5,
    ):
        super().__init__(k=k)
        self.k = k
        self.db_url = db_url
        self.auth_token = auth_token
        self.graph = Graph(db_url, auth_token)

    def _retrieve_passages(self, queries: List[str]) -> List[Node]:
        passages: List[Node] = []

        if not queries:
            return passages

        for query in queries:
            kg = self.graph.search_query(query)
            self.graph.visualize_graph(kg)
            passages.extend(kg.nodes)
        return passages

    def forward(
        self, query_or_queries: Union[str, List[str]], k: Optional[int] = None, **kwargs
    ) -> List[dspy.Prediction]:
        if not isinstance(query_or_queries, list):
            query_or_queries = [query_or_queries]
        passages = self._retrieve_passages(query_or_queries)
        predictions = [
            dspy.Prediction(context=p, long_text=p.attributes) for p in passages
        ]

        return predictions
