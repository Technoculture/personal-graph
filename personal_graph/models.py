"""
Pydantic models for pythonic API to the graph db
"""

from pydantic import BaseModel, Field
from typing import List, Union, Dict, Any


class Node(BaseModel):
    id: Union[int, str] = Field(..., description="Unique Identifier for the node.")
    attributes: Union[str, Dict[Any, Any]] = Field(
        ..., description="Detailed information associated with the node."
    )
    label: str = Field(
        ...,
        min_length=1,
        description="Most related and unique name associated with the node.",
    )


class Edge(BaseModel):
    source: Union[int, str] = Field(
        ..., description="identifier of the source node from which the edge originates."
    )
    target: Union[int, str] = Field(
        ..., description="identifier of the target node to which the edge points."
    )
    label: str = Field(
        ...,
        min_length=1,
        description="Most related and unique name associated with the edge.",
    )
    attributes: Union[str, Dict[Any, Any]] = Field(
        ...,
        description="Detailed information associated with the relationships.",
    )


class EdgeInput(BaseModel):
    source: Node = Field(..., description="Source node from which the edge originates.")
    target: Node = Field(..., description="Target node to which the edge points.")
    label: str = Field(
        ...,
        min_length=1,
        description="Most related and unique name associated with the edge.",
    )
    attributes: Union[str, Dict[Any, Any]] = Field(
        ...,
        description="Detailed information associated within the relationships.",
    )


class KnowledgeGraph(BaseModel):
    nodes: List[Node] = Field(..., default_factory=list)
    edges: List[Edge] = Field(..., default_factory=list)
