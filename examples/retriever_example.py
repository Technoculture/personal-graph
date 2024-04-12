import logging
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from personal_graph.retriever import PersonalRM


def main(db_url, auth_token):
    query = "What is the similarity between Jack and Ronaldo?"

    retriever = PersonalRM(
        db_url=db_url,
        auth_token=auth_token,
    )

    passages = retriever.forward(query)

    logging.info("Retrieved Results: ")
    for passage in passages:
        logging.info(passage)


if __name__ == "__main__":
    load_dotenv()
    db_url = os.getenv("LIBSQL_URL")
    auth_token = os.getenv("LIBSQL_AUTH_TOKEN")

    logging.basicConfig(
        level=logging.DEBUG,
    )

    main(db_url, auth_token)
