import sys
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

script_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
sys.path.append(parent_dir)

from libsql_graph_db import database as db  # noqa: E402
from libsql_graph_db import natural as nt  # noqa: E402


def measure_execution_time(operation_func, *args, **kwargs):
    start_time = time.time()
    res = operation_func(*args, **kwargs)
    end_time = time.time()
    time_taken = end_time - start_time
    return res, time_taken


def time_complexity():
    """
    Main Function to calculate the time duration of each operation.
    """

    operations = [
        (db.find_node, "Student"),
        (db.find_nodes, [db._generate_clause("subject", predicate="LIKE")], ("Civil%")),
        (db.add_node, {"subject": "CSE", "type": ["person", "PHD"]}, "Professor"),
        (
            db.add_nodes,
            [
                {"name": "Stanley", "age": "20"},
                {"name": "Jenny", "age": "55"},
            ],
            ["Student", "Principal"],
        ),
        (db.upsert_node, {"name": "Bob", "age": "23"}, "Student"),
        (
            db.upsert_nodes,
            [
                {"name": "Stanley", "age": "30"},
                {"name": "James", "age": "35"},
            ],
            ["Student", "Professor"],
        ),
        (db.connect_nodes, "Professor", "Student", {"teaches": "CS"}),
        (
            db.connect_many_nodes,
            ["Professor", "Student"],
            ["Student", "Principal"],
            [{"teaches": "CS"}, {"type": "intelligent"}],
        ),
        (db.remove_node, "Professor"),
        (db.remove_nodes, "Engineer"),
        (
            db.traverse,
            os.getenv("LIBSQL_URL"),
            os.getenv("LIBSQL_AUTH_TOKEN"),
            "Student",
        ),
        (nt.insert_into_graph, "I am feeling quite dizzy."),
        (nt.search_from_graph, "What precautions to take in dizziness?"),
    ]

    results_dict = {}

    for operation, *args in operations:
        try:
            result, duration = measure_execution_time(operation, *args)
            operation_name = operation.__name__
            results_dict[operation_name] = duration
        except Exception as err:
            logging.error(f"Exception: {err}")

    logging.info(results_dict)


if __name__ == "__main__":
    logging.basicConfig(
        filename="./log/operations.log", level=logging.DEBUG, filemode="w"
    )

    time_complexity()
