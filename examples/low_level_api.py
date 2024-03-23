#! /usr/bin/python
import os
from dotenv import load_dotenv
from libsql_graph_db import database as db
from libsql_graph_db import visualizers


def insert_single_node(db_url, auth_token, new_node, new_node_id):
    try:
        db.atomic(db_url, auth_token, db.add_node(new_node, new_node_id))
    except Exception as e:
        assert False


def bulk_insert_operations(db_url, auth_token, nodes):
    ids = []
    bodies = []
    for id, body in nodes.items():
        ids.append(id)
        bodies.append(body)

    db.atomic(db_url, auth_token, db.add_nodes(bodies, ids))


def find_a_node(db_url, auth_token, node):
    return db.atomic(db_url, auth_token, db.find_node(node))


def bulk_upsert(db_url, auth_token, nodes):
    ids = []
    bodies = []
    for id, body in nodes.items():
        ids.append(id)
        bodies.append(body)

    db.atomic(db_url, auth_token, db.upsert_nodes(bodies, ids))


def single_upsert(db_url, auth_token, body, id):
    db.atomic(db_url, auth_token, db.upsert_node(id, body))


def bulk_node_connect(db_url, auth_token, edges):
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

    db.atomic(db_url, auth_token, db.connect_many_nodes(sources, targets, properties))


def single_node_connect(db_url, auth_token, source, target, property):
    db.atomic(db_url, auth_token, db.connect_nodes(source, target, property))


def remove_bulk_nodes(db_url, auth_token, ids):
    db.atomic(db_url, auth_token, db.remove_nodes(ids))


def remove_single_node(db_url, auth_token, id):
    db.atomic(db_url, auth_token, db.remove_node(id))


def traverse_nodes(db_url, auth_token, src, tgt=None):
    return db.traverse(db_url, auth_token, src, tgt)


def main(db_url, auth_token, file_path, path_with_bodies):
    # Initialize the Database
    db.initialize(db_url, auth_token)

    new_node = {"subject": "MES", "type": ["person", "Dr"]}
    new_node_id = 4

    # Insert a node into database
    insert_single_node(db_url, auth_token, new_node, new_node_id)

    new_nodes = {2: {"name": "Peri", "age": "90"}, 3: {"name": "Pema", "age": "66"}}

    # Bulk Insert
    bulk_insert_operations(db_url, auth_token, new_nodes)

    # Search a node
    find_a_node(db_url, auth_token, 4)

    nodes = {
        1: {"name": "Stanley", "age": "30"},
        2: {"name": "Sheeran", "type": ["singer", "rich"]},
    }

    # Bulk Update
    bulk_upsert(db_url, auth_token, nodes)

    body = {"name": "Sheeran", "type": ["singer", "rich"]}
    id = 2

    # Update a single node
    single_upsert(db_url, auth_token, body, id)

    edges = {2: [(3, {"wealth": "1000 Billion"}), (2, {"balance": "1000 rupees"})]}

    # Connect bulk nodes
    bulk_node_connect(db_url, auth_token, edges)

    source = 3
    target = 1
    property = {"relation": "enemy"}

    single_node_connect(db_url, auth_token, source, target, property)

    # Remove nodes
    remove_bulk_nodes(db_url, auth_token, [1, 2])
    remove_single_node(db_url, auth_token, 4)

    traverse_nodes(db_url, auth_token, 3, 2)

    # To generate a query clause and find nodes
    kv_name_like = db._generate_clause("name", predicate="LIKE")
    print(db.atomic(db_url, auth_token, db.find_nodes([kv_name_like], ("Pe%",))))

    # Graph Visualization
    visualizers.graphviz_visualize(db_url, auth_token, file_path, ["3"])
    with_bodies = db.traverse(db_url, auth_token, 2, with_bodies=True)
    visualizers.graphviz_visualize_bodies(path_with_bodies, with_bodies)


if __name__ == "__main__":
    load_dotenv()
    db_url = os.getenv("LIBSQL_URL")
    auth_token = os.getenv("LIBSQL_AUTH_TOKEN")

    path1 = "./dotfile.got"
    path2 = "./dotfile_with_bodies.dot"

    main(db_url, auth_token, path1, path2)
