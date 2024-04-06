import logging
import os
from personal_graph.graph import Graph
from personal_graph.models import Node, EdgeInput


def main(url, token):
    with Graph(url, token) as graph:
        # Define nodes and edges
        node1 = Node(id=3, label="Person", attribute={"name": "Alice", "age": "30"})
        node2 = Node(id=4, label="Person", attribute={"name": "Bob", "age": "25"})
        node3 = Node(
            id=1,
            label="Diabetes",
            attribute={"body": "Continuous urination and weight loss"},
        )
        node4 = Node(
            id=2,
            label="Dizziness",
            attribute={"body": "Jack is feeling stressed and feeling quite dizzy."},
        )

        edge1 = EdgeInput(
            source=node1, target=node2, label="KNOWS", attribute={"since": "2015"}
        )

        edge2 = EdgeInput(
            source=node3, target=node2, label="KNOWS", attribute={"since": "2015"}
        )
        edge3 = EdgeInput(
            source=node1, target=node4, label="KNOWS", attribute={"since": "2015"}
        )

        graph.add_node(node1)
        graph.add_nodes([node1, node2])
        graph.add_edge(edge1)

        graph.add_edges([edge2, edge3])

        logging.info(graph.traverse("3"))
        graph.remove_node(3)
        graph.remove_nodes([1, 2])

        graph.update_node(node3)
        node5 = Node(id=18, label="Person", attribute={"name": "Charlie", "age": "35"})
        graph.update_nodes([node4, node5])

        logging.info(graph.search_node(1))

        graph.merge_by_similarity(threshold=0.9)
        logging.info("Merged nodes")

        # Insert query into graph db
        graph.insert(
            text="My brother is actually pretty interested in coral reefs near Sri Lanka."
        )
        logging.info(graph.search_query(text="Who is more interested in coral refs"))

        logging.info(graph.find_nodes_like(label="relative", threshold=0.9))

        graph.save()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/pythonic_api.log",
    )

    db_url = os.getenv("LIBSQL_URL")
    auth_token = os.getenv("LIBSQL_AUTH_TOKEN")

    main(db_url, auth_token)
