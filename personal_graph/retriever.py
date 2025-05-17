import dspy  # type: ignore
from typing import List, Optional, Union
from personal_graph.graph import GraphDB, Node
from dotenv import load_dotenv

load_dotenv()


class PersonalRM(dspy.Retrieve):
    def __init__(
        self,
        graph: GraphDB,
        k: int = 5,
    ):
        super().__init__(k=k)
        self.k = k
        self.graph = graph

    def _retrieve_passages(self, queries: List[str], k: Optional[int] = None) -> List[Node]:
        passages: List[Node] = []

        if not queries:
            return passages

        limit = k if k is not None else self.k

        for query in queries:
            kg = self.graph.search_from_graph(query, limit=limit)
            passages.extend(kg.nodes)
        return passages

    def forward(
        self, query_or_queries: Union[str, List[str]], k: Optional[int] = None, **kwargs
    ) -> List[dspy.Prediction]:
        if not isinstance(query_or_queries, list):
            query_or_queries = [query_or_queries]
        passages = self._retrieve_passages(query_or_queries, k)
        predictions = [
            dspy.Prediction(context=p, long_text=p.attributes) for p in passages
        ]

        return predictions
