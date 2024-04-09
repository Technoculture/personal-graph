import os
import sys
from typing import Any, List, Union

import backoff
from openai import (
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
    UnprocessableEntityError,
)

import dspy
from dsp.utils import dotdict
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from personal_graph.graph import Graph  # noqa: E402


class Embedder:
    def __init__(self, provider: str, model: str):
        if provider == "openai":
            api_key = os.getenv("OPEN_API_KEY")
            if not api_key:
                raise ValueError("Environment variable OPENAI_API_KEY must be set")
            self.client = OpenAI(api_key=api_key)
            self.model = model

    @backoff.on_exception(
        backoff.expo,
        (
            APITimeoutError,
            InternalServerError,
            RateLimitError,
            UnprocessableEntityError,
        ),
        max_time=15,
    )
    def __call__(self, queries) -> Any:
        embedding = self.client.embeddings.create(input=queries, model=self.model)
        return [result.embedding for result in embedding.data]


class Retriever(dspy.Retrieve):
    def __init__(
        self,
        db_url: str,
        auth_token: str,
        k: int = 5,
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-ada-002",
    ):
        self.k = k
        self.embedder = Embedder(embedding_provider, embedding_model)
        self.db_url = db_url
        self.auth_token = auth_token
        self.graph = Graph(db_url, auth_token)

    def _retrieve_passages(self, queries: List[str]) -> List[dotdict]:
        passages = []
        for query in queries:
            kg = self.graph.search_query(query)
            passages.extend(kg.nodes)
        return passages

    def retrieve(self, queries: Union[str, List[str]]) -> List[dotdict]:
        if isinstance(queries, str):
            queries = [queries]
        query_vectors = self.embedder(queries)
        passages = self._retrieve_passages(query_vectors)
        return passages
