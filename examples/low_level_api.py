#! /usr/bin/python
import os
import logging
import argparse
from dotenv import load_dotenv
from libsql_graph_db import database as db
from libsql_graph_db import visualizers


def insert_single_node(db_url, auth_token, new_node, new_node_id):
    try:
        db.atomic(db.add_node(new_node, new_node_id), db_url, auth_token)
    except Exception as e:
        logging.info(f"Exception: {e}")


def bulk_insert_operations(db_url, auth_token, nodes):
    ids = []
    bodies = []
    for id, body in nodes.items():
        ids.append(id)
        bodies.append(body)

    db.atomic(db.add_nodes(bodies, ids), db_url, auth_token)


def find_a_node(db_url, auth_token, node):
    return db.atomic(db.find_node(node), db_url, auth_token)


def bulk_upsert(db_url, auth_token, nodes):
    ids = []
    bodies = []
    for id, body in nodes.items():
        ids.append(id)
        bodies.append(body)

    db.atomic(db.upsert_nodes(bodies, ids), db_url, auth_token)


def single_upsert(db_url, auth_token, body, id):
    db.atomic(db.upsert_node(id, body), db_url, auth_token)


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

    db.atomic(db.connect_many_nodes(sources, targets, properties), db_url, auth_token)


def single_node_connect(db_url, auth_token, source, target, property):
    db.atomic(db.connect_nodes(source, target, property), db_url, auth_token)


def remove_bulk_nodes(db_url, auth_token, ids):
    db.atomic(db.remove_nodes(ids), db_url, auth_token)


def remove_single_node(db_url, auth_token, id):
    db.atomic(db.remove_node(id), db_url, auth_token)


def traverse_nodes(db_url, auth_token, src, tgt):
    return db.traverse(db_url, auth_token, src, tgt)


def main(args):
    # Initialize the Database
    db.initialize(args.url, args.auth_token)

    new_node = {"subject": "MES", "type": ["person", "Dr"]}
    new_node_id = 4

    # Insert a node into database
    insert_single_node(args.url, args.auth_token, new_node, new_node_id)

    new_nodes = {2: {"name": "Peri", "age": "90"}, 3: {"name": "Pema", "age": "66"}}

    # Bulk Insert
    bulk_insert_operations(args.url, args.auth_token, new_nodes)

    # Search a node
    logging.info(f"Found Node: {find_a_node(args.url, args.auth_token, 4)}")

    nodes = {
        1: {"name": "Stanley", "age": "30"},
        2: {"name": "Sheeran", "type": ["singer", "rich"]},
    }

    # Bulk Update
    bulk_upsert(args.url, args.auth_token, nodes)

    body = {"name": "Sheeran", "type": ["singer", "rich"]}
    id = 2

    # Update a single node
    single_upsert(args.url, args.auth_token, body, id)

    edges = {2: [(3, {"wealth": "1000 Billion"}), (2, {"balance": "1000 rupees"})]}

    # Connect bulk nodes
    bulk_node_connect(args.url, args.auth_token, edges)

    source = 3
    target = 1
    property = {"relation": "enemy"}

    single_node_connect(args.url, args.auth_token, source, target, property)

    # Remove nodes
    remove_bulk_nodes(args.url, args.auth_token, [1, 2])
    remove_single_node(args.url, args.auth_token, 4)

    logging.info(f"Traversal result: {traverse_nodes(args.url, args.auth_token, 3, 2)}")

    # To generate a query clause and find nodes
    kv_name_like = db._generate_clause("name", predicate="LIKE")
    logging.info(
        (db.atomic(db.find_nodes([kv_name_like], ("Pe%",)), args.url, args.auth_token))
    )

    # Graph visualization
    visualizers.graphviz_visualize(args.url, args.auth_token, args.file_path, ["3"])
    with_bodies = db.traverse(args.url, args.auth_token, 2, with_bodies=True)
    visualizers.graphviz_visualize_bodies(args.path_with_bodies, with_bodies)


if __name__ == "__main__":
    load_dotenv()
    db_url = os.getenv("LIBSQL_URL")
    auth_token = os.getenv("LIBSQL_AUTH_TOKEN")

    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/low_level_api.log",
    )

    parser = argparse.ArgumentParser(
        description="Shows simple example of low level apis."
    )
    parser.add_argument("--url", default=db_url, type=str)
    parser.add_argument("--auth-token", default=auth_token, type=str)
    parser.add_argument("--file-path", default="./dotfiles.dot", type=str)
    parser.add_argument(
        "--path-with-bodies", default="./path_with_bodies.dot", type=str
    )

    arguments = parser.parse_args()

    main(arguments)
