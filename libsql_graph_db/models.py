"""
Pydantic models for pythonic API to the graph db
"""

from pydantic import BaseModel, Field
from typing import List, Union


class Node(BaseModel):
    id: Union[int, str] = Field(..., description="Unique Identifier for the node.")
    body: str = Field(
        ..., description="Content or information associated with the node."
    )
    label: str = Field(..., description="Label or name associated with the node.")


class Edge(BaseModel):
    source: Union[int, str] = Field(
        ..., description="identifier of the source node from which the edge originates."
    )
    target: Union[int, str] = Field(
        ..., description="identifier of the target node to which the edge points."
    )
    label: str = Field(..., description="Label or property associated with the edge.")


class KnowledgeGraph(BaseModel):
    nodes: List[Node] = Field(..., default_factory=list)
    edges: List[Edge] = Field(..., default_factory=list)
