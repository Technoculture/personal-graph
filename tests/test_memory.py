from personal_graph.memory import MemoryManager
from personal_graph.models import Node


def test_memory_store_and_recall(graph, mock_db_connection_and_cursor):
    memory = MemoryManager(graph)
    memory.store_event("Alice likes Bob", {"tag": "test"})

    results = memory.recall("Alice", k=1)
    assert isinstance(results, list)
    if results:
        assert isinstance(results[0], Node)
