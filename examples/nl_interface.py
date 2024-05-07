#! /usr/bin/python
import os
import logging
import argparse
from dotenv import load_dotenv
from personal_graph import Graph, LLMClient, EmbeddingClient, DatabaseConfig


def main(args):
    llm_client = LLMClient()
    embedding_client = EmbeddingClient()
    with Graph(
        database_config=DatabaseConfig(
            db_url=args.db_url, db_auth_token=args.db_auth_token
        ),
        llm_client=llm_client,
        embedding_model_client=embedding_client,
    ) as graph:
        # Testing insert query into graph db
        nl_query = "increased thirst, weight loss, increased hunger, frequent urination etc. are all symptoms of diabetes."
        kg = graph.insert_into_graph(text=nl_query)

        logging.info("Nodes in the Knowledge Graph: \n")
        for node in kg.nodes:
            logging.info(
                f"ID: {node.id}, Label: {node.label}, Attribute: {node.attributes}"
            )

        logging.info("Edges in the Knowledge Graph: \n")
        for edge in kg.edges:
            logging.info(
                f"Source: {edge.source}, Target: {edge.target}, Label: {edge.label}, Attribute: {edge.attributes}"
            )

        # Testing search query from graph db
        search_query = "I am losing my weight too frequent."
        knowledge_graph = graph.search_from_graph(search_query)

        logging.info(f"Knowledge Graph: \n{knowledge_graph}")


if __name__ == "__main__":
    load_dotenv()

    logging.basicConfig(
        level=logging.DEBUG,
        filemode="w",
        filename="./log/nl_interface.log",
    )

    parser = argparse.ArgumentParser(
        description="Shows simple example of natural language apis."
    )
    parser.add_argument("--db-url", default=os.getenv("LIBSQL_URL"), type=str)
    parser.add_argument(
        "--db-auth-token", default=os.getenv("LIBSQL_AUTH_TOKEN"), type=str
    )

    arguments = parser.parse_args()

    main(arguments)
