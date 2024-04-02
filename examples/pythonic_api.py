import logging
import os
from libsql_graph_db.graph import Graph
from libsql_graph_db.models import Node, Edge


def main(url, token):
    with Graph(url, token) as graph:
        # Define nodes and edges
        node1 = Node(id=3, label="Person", attribute={"name": "Alice", "age": "30"})
        node2 = Node(id=4, label="Person", attribute={"name": "Bob", "age": "25"})
        edge = Edge(
            source=node1.id, target=node2.id, label="KNOWS", attribute={"since": "2015"}
        )

        graph.add_node(node1)
        graph.add_nodes([node1, node2])
        graph.add_edge(edge)

        logging.info(graph.traverse("3"))
        graph.remove_node(3)

        node3 = Node(id=18, label="Person", attribute={"name": "Charlie", "age": "35"})
        graph.upsert_node(node3)

        logging.info(graph.search_node(1))

        # Insert query into graph db
        graph.insert(
            text="My brother is actually pretty interested in coral reefs near Sri Lanka."
        )
        logging.info(graph.search_query(text="Who is more interested in coral refs"))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/pythonic_api.log",
    )

    db_url = os.getenv("LIBSQL_URL")
    auth_token = os.getenv("LIBSQL_AUTH_TOKEN")

    main(db_url, auth_token)
