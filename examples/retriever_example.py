import logging
import os
from dotenv import load_dotenv
from personal_graph.retriever import PersonalRM


def main(db_url, db_auth_token):
    query = "What is the similarity between Jack and Ronaldo?"

    retriever = PersonalRM(
        db_url=db_url,
        db_auth_token=db_auth_token,
    )

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
