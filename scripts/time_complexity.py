# import sys
# import os
# import time
# import logging
# from dotenv import load_dotenv
#
# load_dotenv()
#
# script_dir = os.path.dirname(os.path.realpath(__file__))
# parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
# sys.path.append(parent_dir)
#
# # from personal_graph import database as db  # noqa: E402
# # from personal_graph import natural as nt  # noqa: E402
#
#
# def measure_execution_time(operation_func, *args, **kwargs):
#     start_time = time.time()
#     res = operation_func(*args, **kwargs)
#     end_time = time.time()
#     time_taken = end_time - start_time
#     return res, time_taken
#
#
# def time_complexity():
#     """
#     Main Function to calculate the time duration of each operation.
#     """
#
#     operations = [
#         (db.find_node, "Student"),
#         (db.find_nodes, [db._generate_clause("subject", predicate="LIKE")], ("Civil%")),
#         (db.add_node, {"subject": "CSE", "type": ["person", "PHD"]}, 3),
#         (
#             db.add_nodes,
#             [
#                 {"name": "Stanley", "age": "20"},
#                 {"name": "Jenny", "age": "55"},
#             ],
#             [1, 2],
#             ["Student", "Principal"],
#         ),
#         (db.upsert_node, 1, "Student", {"name": "Bob", "age": "23"}),
#         (
#             db.upsert_nodes,
#             [
#                 {"name": "Stanley", "age": "30"},
#                 {"name": "James", "age": "35"},
#             ],
#             ["Professor", "Doctor"],
#             [1, 2],
#         ),
#         (db.connect_nodes, 2, 1, "teaches", {"subject": "CS"}),
#         (
#             db.connect_many_nodes,
#             [2, 3],
#             [1, 3],
#             ["Has", "is"],
#             [{"disease": "Diabetes"}, {"patient": "Diabetes Symptoms"}],
#         ),
#         (db.remove_node, 1),
#         (db.remove_nodes, [1, 2]),
#         (
#             db.traverse,
#             os.getenv("LIBSQL_URL"),
#             os.getenv("LIBSQL_AUTH_TOKEN"),
#             2,
#         ),
#         (db.vector_search_node, {"body": "Jack has diabetic symptoms"}, 0.9),
#         (db.vector_search_edge, {"relation": "Has"}),
#         (db.find_similar_nodes, "relative", 0.9),
#         (db.pruning, 0.9),
#         (nt.insert_into_graph, "I am feeling quite dizzy."),
#         (nt.search_from_graph, "What precautions to take in dizziness?"),
#     ]
#
#     results_dict = {}
#
#     for operation, *args in operations:
#         try:
#             result, duration = measure_execution_time(operation, *args)
#             operation_name = operation.__name__
#             results_dict[operation_name] = duration
#         except Exception as err:
#             logging.error(f"Exception: {err}")
#
#     logging.info(results_dict)
#
#
# if __name__ == "__main__":
#     logging.basicConfig(
#         filename="./log/operations.log", level=logging.DEBUG, filemode="w"
#     )
#
#     time_complexity()
