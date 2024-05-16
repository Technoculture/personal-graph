import argparse
import os
import logging
from personal_graph import (
    Graph,
    Node,
    KnowledgeGraph,
    Edge,
    LLMClient,
    EdgeInput,
    EmbeddingClient,
)
from personal_graph.database import SQLiteVSS, TursoDB
from personal_graph.graph_generator import InstructorGraphGenerator
from personal_graph.ml import networkx_to_pg, pg_to_networkx


def main(args):
    vector_store = SQLiteVSS(
        persistence_layer=TursoDB(url=args.db_url, auth_token=args.db_auth_token),
        embedding_model_client=EmbeddingClient(),
    )
    with Graph(
        vector_store=vector_store,
        graph_generator=InstructorGraphGenerator(llm_client=LLMClient()),
    ) as graph:
        # Define nodes and edges
        node1 = Node(
            id="3", label="close relative", attributes={"name": "Alice", "age": "30"}
        )
        node2 = Node(id="4", label="relative", attributes={"name": "Bob", "age": "25"})
        node3 = Node(
            id="1",
            label="Diabetes",
            attributes={"body": "Continuous urination and weight loss"},
        )
        node4 = Node(
            id="2",
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

        # Insert information about conversations with the user over time
        graph.insert(
            text="User talked about their childhood dreams and aspirations.",
            attributes={
                "date": "2023-01-15",
                "topic": "childhood dreams",
                "depth_score": 3,
            },
        )

        graph.insert(
            text="User discussed their fears and insecurities in their current relationship.",
            attributes={
                "date": "2023-02-28",
                "topic": "relationship fears",
                "depth_score": 4,
            },
        )

        graph.insert(
            text="User shared their spiritual beliefs and existential questions.",
            attributes={
                "date": "2023-03-10",
                "topic": "spirituality and existence",
                "depth_score": 5,
            },
        )

        graph.insert(
            text="User mentioned their favorite hobbies and weekend activities.",
            attributes={"date": "2023-04-02", "topic": "hobbies", "depth_score": 2},
        )

        query = "User talked about his fears, achievements, hobbies and beliefs."

        deepest_conversation = graph.search(
            query, descending=False, limit=1, sort_by="depth_score"
        )

        if deepest_conversation:
            logging.info(f"Question: {query}")
            logging.info(
                f"Answer: Our deepest conversation was on {deepest_conversation['date']} when we discussed {deepest_conversation['topic']}."
            )
        else:
            logging.info(f"Question: {query}")
            logging.info(
                "Answer: I apologize, but I don't have enough information to determine our deepest conversation."
            )

        graph.insert_into_graph(text="Alice is Bob's sister. Bob works at Google.")

        # Retrieve relevant information from the graph
        query = "Who is Alice?"
        results = graph.search(
            query,
            limit=1,
        )
        logging.info(results)

        if results is not None:
            logging.info(results)

        query = "Where does Bob work?"
        results = graph.search(query, limit=1)
        logging.info(results)
        if results is not None:
            logging.info(results["body"])

        graph.add_node(node1)
        graph.add_nodes([node3, node2])
        graph.add_edge(edge1)
        graph.add_edges([edge2, edge3])

        logging.info(graph.traverse("3"))
        graph.remove_node(1)
        graph.remove_nodes([1, 2])
        logging.info(graph.search_node("3"))

        node5 = Node(
            id="3",
            label="Asthma",
            attributes={"body": "Respiratory disease"},
        )
        graph.update_node(node5)
        node5 = Node(id=18, label="Person", attributes={"name": "Charlie", "age": "35"})
        graph.update_nodes([node4, node5])

        logging.info(graph.search_node(4))

        graph.merge_by_similarity(threshold=5000)
        logging.info("Merged nodes")

        # Insert natural language query into graph db
        graph.insert_into_graph(
            text="My brother is actually pretty interested in coral reefs near Sri Lanka."
        )

        # Search natural language query from graph db
        kg = graph.search_from_graph(text="Who is more interested in coral refs")
        graph.visualize_graph(kg).render("sample.dot")
        logging.info(
            graph.search_from_graph(text="Who is more interested in coral refs")
        )

        logging.info(graph.find_nodes_like(label="relative", threshold=3000))

        graph.visualize("sample.dot", ["4"])
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

        # Transforms to and from networkx do not alter the graph
        g2 = networkx_to_pg(
            pg_to_networkx(graph, post_visualize=True),
            graph,
            post_visualize=True,
            override=True,
        )
        if graph == g2:
            logging.info("TRUE")
        assert graph == g2


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/pythonic_api.log",
    )

    parser = argparse.ArgumentParser(
        description="Shows simple example of high level apis."
    )

    parser.add_argument("--db-url", default=os.getenv("LIBSQL_URL"), type=str)
    parser.add_argument(
        "--db-auth-token", default=os.getenv("LIBSQL_AUTH_TOKEN"), type=str
    )

    arguments = parser.parse_args()
    main(arguments)
