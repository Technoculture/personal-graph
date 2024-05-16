import logging
import os
from dotenv import load_dotenv

from personal_graph import Graph, LLMClient, EmbeddingClient, PersonalRM
from personal_graph.database import SQLiteVSS, TursoDB
from personal_graph.graph_generator import InstructorGraphGenerator


def main(db_url, db_auth_token):
    vector_store = SQLiteVSS(
        persistence_layer=TursoDB(
            url=db_url,
            auth_token=db_auth_token,
        ),
        embedding_model_client=EmbeddingClient(),
    )

    with Graph(
        vector_store=vector_store,
        graph_generator=InstructorGraphGenerator(llm_client=LLMClient()),
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
