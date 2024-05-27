from pydantic import BaseModel
from typing import Any, Dict, List

class Node(BaseModel):
    id: int | str
    attributes: str | Dict[Any, Any]
    label: str

class Edge(BaseModel):
    source: int | str
    target: int | str
    label: str
    attributes: str | Dict[Any, Any]

class EdgeInput(BaseModel):
    source: Node
    target: Node
    label: str
    attributes: str | Dict[Any, Any]

class KnowledgeGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
