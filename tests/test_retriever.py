import pytest
from personal_graph import GraphDB, PersonalRM, KnowledgeGraph, Node
from unittest.mock import patch


def test_forward_uses_provided_k(graph):
    retriever = PersonalRM(graph, k=3)
    kg = KnowledgeGraph(nodes=[Node(id=1, label="a", attributes="a")], edges=[])
    with patch.object(graph, "search_from_graph", return_value=kg) as mock_search:
        retriever.forward("q", k=1)
        mock_search.assert_called_with("q", limit=1)


def test_forward_defaults_to_self_k(graph):
    retriever = PersonalRM(graph, k=2)
    kg = KnowledgeGraph(nodes=[Node(id=1, label="a", attributes="a")], edges=[])
    with patch.object(graph, "search_from_graph", return_value=kg) as mock_search:
        retriever.forward("q")
        mock_search.assert_called_with("q", limit=2)
