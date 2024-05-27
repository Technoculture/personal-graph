from pathlib import Path
from personal_graph.clients import LiteLLMEmbeddingClient as LiteLLMEmbeddingClient
from personal_graph.embeddings import OpenAIEmbeddingsModel as OpenAIEmbeddingsModel
from personal_graph.database.sqlite.sqlite import SQLite as SQLite
from personal_graph.database.tursodb.turso import TursoDB as TursoDB
from personal_graph.vector_store.vector_store import (
    VectorStore as VectorStore,
)
import libsql_experimental as libsql  # type: ignore
from typing import Any, Dict, Callable, Union
from personal_graph.persistence_layer.database.db import CursorExecFunction

def read_sql(sql_file: Path) -> str: ...

class SQLiteVSS(VectorStore):
    db: Union[TursoDB, SQLite]
    embedding_model: LiteLLMEmbeddingClient
    def __init__(
        self, *, db: TursoDB | SQLite, embedding_client: LiteLLMEmbeddingClient = ...
    ) -> None: ...
    def initialize(self): ...
    def save(self): ...
    def add_node_embedding(
        self, id: Any, label: str, attribute: Dict[Any, Any]
    ) -> None: ...
    def add_edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict
    ) -> None: ...
    def add_edge_embeddings(self, sources, targets, labels, attributes) -> None: ...
    def delete_node_embedding(self, id: Any) -> None: ...
    def delete_edge_embedding(self, ids: Any) -> None: ...
    def vector_search_node(
        self,
        data: Dict,
        *,
        threshold: float = 0.9,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ): ...
    def vector_search_edge(
        self,
        data: Dict,
        *,
        threshold: float = 0.9,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ): ...
    def vector_search_node_from_multi_db(
        self, data: Dict, *, threshold: float = 0.9, limit: int = 1
    ): ...
    def vector_search_edge_from_multi_db(
        self, data: Dict, *, threshold: float = 0.9, limit: int = 1
    ): ...
