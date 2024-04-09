import os
import sys
from typing import List, Optional, Union

import dspy  # type: ignore
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from personal_graph.graph import Graph  # noqa: E402
from personal_graph.models import Node  # noqa: E402


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
            passages.extend(kg.nodes)
        return passages

    def forward(
        self, query_or_queries: Union[str, List[str]], k: Optional[int] = None, **kwargs
    ) -> list[Node]:
        if not isinstance(query_or_queries, list):
            query_or_queries = [query_or_queries]
        passages = self._retrieve_passages(query_or_queries)
        return passages
