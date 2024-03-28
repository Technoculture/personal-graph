"""
Pydantic models for pythonic API to the graph db
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class Node(BaseModel):
    node_identifier: str = Field(
        ..., description="Unique Identifier which defines the node."
    )
    body: str = Field(
        ..., description="Content or information associated with the node."
    )
    label: Optional[str] = Field(
        None, description="Label or name associated with the node."
    )
    color: Optional[str] = Field(
        "gray", description="Color representation of the node."
    )


class Edge(BaseModel):
    id: int = Field(..., description="Unique identifier for the edge.")
    source: str = Field(
        ..., description="identifier of the source node from which the edge originates."
    )
    target: str = Field(
        ..., description="identifier of the target node to which the edge points."
    )
    label: str = Field(..., description="Label or property associated with the edge.")
    color: Optional[str] = Field(
        "black", description="Color representation of the edge."
    )


class KnowledgeGraph(BaseModel):
    nodes: List[Node] = Field(..., default_factory=list)
    edges: List[Edge] = Field(..., default_factory=list)
