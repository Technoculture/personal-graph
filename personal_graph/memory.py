from __future__ import annotations

from typing import Dict, List, Optional

from personal_graph import GraphDB, Node


class MemoryManager:
    """Lightweight interface for storing and recalling textual events."""

    def __init__(self, graph_db: Optional[GraphDB] = None) -> None:
        self.graph = graph_db or GraphDB()

    def __enter__(self) -> "MemoryManager":
        self.graph.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.graph.__exit__(exc_type, exc_value, traceback)

    def store_event(self, text: str, metadata: Dict) -> None:
        """Store an event description with associated metadata."""
        self.graph.insert(text, metadata)

    def recall(self, query: str, k: int = 5) -> List[Node]:
        """Recall up to ``k`` events most relevant to ``query``."""
        results = self.graph.search(query, limit=k)
        if not results:
            return []
        nodes: List[Node] = []
        for row in results:
            nodes.append(Node(id=row[1], label=row[2], attributes=row[3]))
        return nodes
