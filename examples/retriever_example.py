import logging
import os
from dotenv import load_dotenv

from personal_graph import Graph, LLMClient, EmbeddingClient, DatabaseConfig, PersonalRM


def main(db_url, db_auth_token):
    with Graph(
        database_config=DatabaseConfig(db_url=db_url, db_auth_token=db_auth_token),
        llm_client=LLMClient(),
        embedding_model_client=EmbeddingClient(),
    ) as graph:
        query = "What is the similarity between Jack and Ronaldo?"
        retriever = PersonalRM(graph)

        passages = retriever.forward(query)

        logging.info("Retrieved Results: ")
        for passage in passages:
            logging.info(passage)


if __name__ == "__main__":
    load_dotenv()
    db_url = os.getenv("LIBSQL_URL")
    db_auth_token = os.getenv("LIBSQL_AUTH_TOKEN")

    logging.basicConfig(
        level=logging.DEBUG,
    )

    main(db_url, db_auth_token)
