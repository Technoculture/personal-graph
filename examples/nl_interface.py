#! /usr/bin/python
import os
import openai
import logging
import argparse
from dotenv import load_dotenv
from personal_graph import database as db
from personal_graph import natural
from personal_graph.embeddings import OpenAIEmbeddingsModel


def main(args):
    # Initialize the Database
    db.initialize(args.url, args.auth_token)

    # LLM client
    llm_client = openai.OpenAI(
        api_key="",
        base_url=args.llm_base_url,
        default_headers={"Authorization": f"Bearer {args.llm_token}"},
    )

    # Embedding client
    embedding_client = (
        openai.OpenAI(
            api_key="",
            base_url=args.embeddings_base_url,
            default_headers={"Authorization": f"Bearer {args.embeddings_token}"},
        )
        if args.embeddings_base_url and args.embeddings_token
        else None
    )

    embedding_model = OpenAIEmbeddingsModel(
        embedding_client, args.embeddings_model_name, args.embedding_model_dimension
    )

    # Testing insert query into graph db
    nl_query = "increased thirst, weight loss, increased hunger, frequent urination etc. are all symptoms of diabetes."
    graph = natural.insert_into_graph(
        text=nl_query,
        llm_client=llm_client,
        llm_model_name=args.llm_model_name,
        embedding_model=embedding_model,
    )

    logging.info("Nodes in the Knowledge Graph: \n")
    for node in graph.nodes:
        logging.info(
            f"ID: {node.id}, Label: {node.label}, Attribute: {node.attributes}"
        )

    logging.info("Edges in the Knowledge Graph: \n")
    for edge in graph.edges:
        logging.info(
            f"Source: {edge.source}, Target: {edge.target}, Label: {edge.label}, Attribute: {edge.attributes}"
        )

    # Testing search query from graph db
    search_query = "I am losing my weight too frequent."
    knowledge_graph = natural.search_from_graph(
        search_query, embedding_model=embedding_model
    )

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
    parser.add_argument("--url", default=os.getenv("LIBSQL_URL"), type=str)
    parser.add_argument(
        "--auth-token", default=os.getenv("LIBSQL_AUTH_TOKEN"), type=str
    )
    parser.add_argument("--llm-base-url", default=os.getenv("LITE_LLM_BASE_URL"))
    parser.add_argument("--llm-token", default=os.getenv("LITE_LLM_TOKEN"), type=str)
    parser.add_argument("--llm-model-name", default="openai/gpt-3.5-turbo", type=str)
    parser.add_argument("--embeddings-base-url", default=os.getenv("LITE_LLM_BASE_URL"))
    parser.add_argument(
        "--embeddings-token", default=os.getenv("LITE_LLM_TOKEN"), type=str
    )
    parser.add_argument(
        "--embeddings-model-name", default="openai/text-embedding-3-small", type=str
    )
    parser.add_argument("--embedding-model-dimension", default=384, type=int)

    arguments = parser.parse_args()

    main(arguments)
