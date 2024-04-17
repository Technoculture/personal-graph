import os
import logging
from personal_graph.graph import Graph
from personal_graph.models import Node, EdgeInput, KnowledgeGraph, Edge


def main(url, token):
    with Graph(url, token) as graph:
        # Define nodes and edges
        node1 = Node(id=3, label="Person", attributes={"name": "Alice", "age": "30"})
        node2 = Node(id=4, label="Person", attributes={"name": "Bob", "age": "25"})
        node3 = Node(
            id=1,
            label="Diabetes",
            attributes={"body": "Continuous urination and weight loss"},
        )
        node4 = Node(
            id=2,
            label="Dizziness",
            attributes={"body": "Jack is feeling stressed and feeling quite dizzy."},
        )

        edge1 = EdgeInput(
            source=node1, target=node2, label="KNOWS", attributes={"since": "2015"}
        )

        edge2 = EdgeInput(
            source=node3, target=node2, label="KNOWS", attributes={"since": "2015"}
        )
        edge3 = EdgeInput(
            source=node1, target=node4, label="KNOWS", attributes={"since": "2015"}
        )

        graph.add_node(node1)
        graph.add_nodes([node1, node2])
        graph.add_edge(edge1)

        graph.add_edges([edge2, edge3])

        logging.info(graph.traverse("3"))
        graph.remove_node(3)
        graph.remove_nodes([1, 2])

        graph.update_node(node3)
        node5 = Node(id=18, label="Person", attributes={"name": "Charlie", "age": "35"})
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

        graph.visualize("sample.dot", ["2"])
        kg = KnowledgeGraph(
            nodes=[
                Node(
                    id="13549727-1612-4b16-b942-492c1e2d9281",
                    attributes='{"body":"Disease","id":"13549727-1612-4b16-b942-492c1e2d9281"}',
                    label="Tuberculosis",
                ),
                Node(
                    id="fc825bd5-313b-41c5-94b6-1f974162dba2",
                    attributes='{"body":"A bacterial infection caused by Mycobacterium tuberculosis that primarily affects the lungs.","id":"fc825bd5-313b-41c5-94b6-1f974162dba2"}',
                    label="Tuberculosis",
                ),
                Node(
                    id="7ccf0900-4380-4421-89b6-ab5e1d586587",
                    attributes='{"body":"An individual receiving medical treatment for a specific condition or disease.","id":"7ccf0900-4380-4421-89b6-ab5e1d586587"}',
                    label="Patient",
                ),
                Node(
                    id="c2d483c0-98ac-45b2-a564-e671dd1dd5fb",
                    attributes='{"body":"Person","id":"c2d483c0-98ac-45b2-a564-e671dd1dd5fb"}',
                    label="Alice",
                ),
                Node(
                    id="ced81c3d-5edd-481a-aa76-319569080240",
                    attributes='{"body":"Action","id":"ced81c3d-5edd-481a-aa76-319569080240"}',
                    label="Suffering",
                ),
            ],
            edges=[
                Edge(
                    source="fc825bd5-313b-41c5-94b6-1f974162dba2",
                    target="7ccf0900-4380-4421-89b6-ab5e1d586587",
                    label="Diagnosis",
                    attributes='{"body":"The identification of Tuberculosis in an individual."}',
                ),
                Edge(
                    source="c2d483c0-98ac-45b2-a564-e671dd1dd5fb",
                    target="ced81c3d-5edd-481a-aa76-319569080240",
                    label="is suffering from",
                    attributes='{"body":"Present Tense Verb"}',
                ),
            ],
        )
        logging.info(graph.visualize_graph(kg))

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
