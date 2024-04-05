import os
import json
import uuid
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from libsql_graph_db.models import Node, Edge, KnowledgeGraph
from libsql_graph_db.database import (
    add_node,
    atomic,
    connect_nodes,
    vector_search_node,
    vector_search_edge,
)

load_dotenv()
if os.getenv("OPEN_API_KEY"):
    client = instructor.patch(OpenAI(api_key=os.getenv("OPEN_API_KEY")))
else:
    client = None
db_url = os.getenv("LIBSQL_URL")
auth_token = os.getenv("LIBSQL_AUTH_TOKEN")


def generate_graph(query: str) -> KnowledgeGraph:
    knowledge_graph = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a high quality knowledge graph generator based on the user query for the purpose of generating descriptive and informative knowledge graphs.",
            },
            {
                "role": "user",
                "content": f"Help me describe this user query as a detailed knowledge graph with proper, meaningful and unique relationships and edges: {query}",
            },
        ],
        response_model=KnowledgeGraph,
    )
    return knowledge_graph


def insert_into_graph(text: str) -> KnowledgeGraph:
    uuid_dict = {}
    kg = generate_graph(text)

    for node in kg.nodes:
        uuid_dict[node.id] = str(uuid.uuid4())
        atomic(
            add_node(node.label, {"body": node.attribute}, uuid_dict[node.id]),
            db_url,
            auth_token,
        )

    for edge in kg.edges:
        atomic(
            connect_nodes(
                uuid_dict[edge.source],
                uuid_dict[edge.target],
                edge.label,
                {"body": edge.attribute},
            ),
            db_url,
            auth_token,
        )

    return kg


def search_from_graph(text: str) -> KnowledgeGraph:
    kg = generate_graph(text)

    nodes_list = []
    edges_list = []

    for node in kg.nodes:
        search_result = atomic(
            vector_search_node({"body": node.attribute}, 1),
            db_url,
            auth_token,
        )
        if search_result is None:
            continue

        new_node_data = (
            search_result[3]
            if isinstance(search_result[3], str)
            else json.dumps({"body": "Mock Node Body"})
        )

        new_node = Node(
            id=search_result[1] if isinstance(search_result, str) else "0",
            attribute=json.loads(new_node_data),
            label=search_result[2]
            if isinstance(search_result, str)
            else "Sample Label",
        )

        if new_node not in nodes_list:
            nodes_list.append(new_node)

    for edge in kg.edges:
        search_result = atomic(
            vector_search_edge(
                {
                    "source_id": edge.source,
                    "target_id": edge.target,
                    "label": edge.label,
                    "attribute": {"body": edge.attribute},
                },
                1,
            ),
            db_url,
            auth_token,
        )
        if search_result is None:
            continue

        new_edge = Edge(
            source=search_result[1],
            target=search_result[2],
            label=search_result[3]
            if isinstance(search_result, str)
            else "Sample label",
            attribute=json.loads(search_result[4])
            if isinstance(search_result[4], str)
            else "Sample Property",
        )

        if new_edge not in edges_list:
            edges_list.append(new_edge)

    knowledge_graph = KnowledgeGraph(nodes=nodes_list, edges=edges_list)

    return knowledge_graph
