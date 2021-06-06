import pytest
import json
from pathlib import Path
from filecmp import cmp
from simple_graph_sqlite import database as db


@pytest.fixture()
def database_test_file(tmp_path):
    d = tmp_path / "simplegraph"
    d.mkdir()
    return str(d / "apple.sqlite")


@pytest.fixture()
def nodes():
    return {
        1: {'name': 'Apple Computer Company', 'type': ['company', 'start-up'], 'founded': 'April 1, 1976'},
        2: {'name': 'Steve Wozniak', 'type': ['person', 'engineer', 'founder']},
        3: {'name': 'Steve Jobs', 'type': ['person', 'designer', 'founder']},
        4: {'name': 'Ronald Wayne', 'type': ['person', 'administrator', 'founder']},
        5: {'name': 'Mike Markkula', 'type': ['person', 'investor']}
    }


@pytest.fixture()
def edges():
    return {
        1: [(4, {'action': 'divested', 'amount': 800, 'date': 'April 12, 1976'})],
        2: [(1, {'action': 'founded'}), (3, None)],
        3: [(1, {'action': 'founded'})],
        4: [(1, {'action': 'founded'})],
        5: [(1, {'action': 'invested', 'equity': 80000, 'debt': 170000})]
    }


@pytest.fixture()
def apple(database_test_file, nodes, edges):
    db.initialize(database_test_file)
    [db.atomic(database_test_file, db.add_node(node, id))
     for id, node in nodes.items()]
    for src, targets in edges.items():
        for target in targets:
            tgt, label = target
            if label:
                db.atomic(database_test_file,
                          db.connect_nodes(src, tgt, label))
            else:
                db.atomic(database_test_file, db.connect_nodes(src, tgt))
    yield


def test_initialize(database_test_file, apple):
    db_file = Path(database_test_file).resolve()
    assert db_file.exists()
    assert db_file.stat().st_size == 28672


def test_bulk_operations(database_test_file, nodes, edges):
    db.initialize(database_test_file)
    ids = []
    bodies = []
    for id, body in nodes.items():
        ids.append(id)
        bodies.append(body)

    # bulk add and confirm
    db.atomic(database_test_file, db.add_nodes(bodies, ids))
    for id, node in nodes.items():
        assert db.atomic(database_test_file, db.find_node(id)) == node
    sources = []
    targets = []
    properties = []
    for src, tgts in edges.items():
        for target in tgts:
            tgt, label = target
            sources.append(src)
            targets.append(tgt)
            if label:
                properties.append(label)
            else:
                properties.append({})

    # bulk connect and confirm
    db.atomic(database_test_file, db.connect_many_nodes(
        sources, targets, properties))
    for src, tgts in edges.items():
        actual = [tuple(json.loads(x) for x in edge) for edge in db.atomic(
            database_test_file, db.get_connections_one_way(src))]
        for target in tgts:
            tgt, label = target
            if label:
                expected = (src, tgt, label)
            else:
                expected = (src, tgt, {})
            assert expected in actual

    # bulk remove and confirm
    db.atomic(database_test_file, db.remove_nodes(ids))
    for id in ids:
        assert db.atomic(database_test_file, db.find_node(id)) == {}


def test_search(database_test_file, apple, nodes):
    for id, node in nodes.items():
        assert db.atomic(database_test_file, db.find_node(id)) == node
    steves = db.atomic(database_test_file, db.find_nodes(
        {'name': 'Steve'}, db._search_like, db._search_starts_with))
    assert len(steves) == 2
    assert list(map(lambda x: x['name'], steves)) == [
        'Steve Wozniak', 'Steve Jobs']


def test_traversal(database_test_file, apple):
    assert db.traverse(database_test_file, 2, 3) == ['2', '1', '3']
    assert db.traverse(database_test_file, 4, 5) == ['4', '1', '2', '3', '5']
    assert db.traverse(database_test_file, 5,
                       neighbors_fn=db.find_inbound_neighbors) == ['5']
    assert db.traverse(database_test_file, 5,
                       neighbors_fn=db.find_outbound_neighbors) == ['5', '1', '4']
    assert db.traverse(database_test_file, 5, neighbors_fn=db.find_neighbors) == [
        '5', '1', '2', '3', '4']


def test_visualization(database_test_file, apple, tmp_path):
    dot_raw = tmp_path / "apple-raw.dot"
    db.visualize(database_test_file, dot_raw, [4, 1, 5])
    here = Path(__file__).parent.resolve()
    assert cmp(dot_raw, here / "fixtures" / "apple-raw.dot")
    dot = tmp_path / "apple.dot"
    db.visualize(database_test_file, dot, [4, 1, 5], exclude_node_keys=[
                 'type'], hide_edge_key=True)
    assert cmp(dot, here / "fixtures" / "apple.dot")
