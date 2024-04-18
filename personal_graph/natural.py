import os
import uuid
import instructor
from graphviz import Digraph  # type: ignore
from openai import OpenAI
from dotenv import load_dotenv
from personal_graph.models import KnowledgeGraph, Node, Edge
from personal_graph.database import (
    add_node,
    atomic,
    connect_nodes,
    vector_search_node,
    vector_search_edge,
    all_connected_nodes,
)

load_dotenv()

if os.getenv("OPEN_API_KEY"):
    client = instructor.patch(OpenAI(api_key=os.getenv("OPEN_API_KEY")))
else:
    client = None

db_url = os.getenv("LIBSQL_URL")
auth_token = os.getenv("LIBSQL_AUTH_TOKEN")


def generate_graph(query: str) -> KnowledgeGraph:
    client = instructor.patch(OpenAI(api_key=os.getenv("OPEN_API_KEY")))
    knowledge_graph = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a high quality knowledge graph generator based on the user query for the purpose of generating descriptive, informative, detailed and accurate knowledge graphs. You can generate proper nodes and edges as a knowledge graph.",
            },
            {
                "role": "user",
                "content": f"Help me describe this user query as a detailed knowledge graph with meaningful relationships that should provide some descriptive attributes(attribute is the detailed and proper information about the edge) and informative labels about the nodes and relationship. Try to make most of the relationships between similar nodes: {query}",
            },
        ],
        response_model=KnowledgeGraph,
    )
    return knowledge_graph


def visualize_knowledge_graph(kg: KnowledgeGraph) -> Digraph:
    dot = Digraph(comment="Knowledge Graph")

    # Add nodes
    for node in kg.nodes:
        dot.node(node.id, node.label, color="black")

    # Add edges
    for edge in kg.edges:
        dot.edge(str(edge.source), str(edge.target), edge.label, color="black")

    return dot


def insert_into_graph(text: str) -> KnowledgeGraph:
    uuid_dict = {}
    kg = generate_graph(text)

    try:
        for node in kg.nodes:
            uuid_dict[node.id] = str(uuid.uuid4())
            atomic(
                add_node(node.label, {"body": node.attributes}, uuid_dict[node.id]),
                os.getenv("LIBSQL_URL"),
                os.getenv("LIBSQL_AUTH_TOKEN"),
            )

        for edge in kg.edges:
            atomic(
                connect_nodes(
                    uuid_dict[edge.source],
                    uuid_dict[edge.target],
                    edge.label,
                    {"body": edge.attributes},
                ),
                os.getenv("LIBSQL_URL"),
                os.getenv("LIBSQL_AUTH_TOKEN"),
            )
    except KeyError:
        return KnowledgeGraph()

    return kg


def search_from_graph(text: str) -> KnowledgeGraph:
    try:
        similar_nodes = atomic(
            vector_search_node({"body": text}, 0.9, 2),
            os.getenv("LIBSQL_URL"),
            os.getenv("LIBSQL_AUTH_TOKEN"),
        )
        similar_edges = atomic(
            vector_search_edge({"body": text}, k=2),
            os.getenv("LIBSQL_URL"),
            os.getenv("LIBSQL_AUTH_TOKEN"),
        )

        resultant_subgraph = KnowledgeGraph()

        if similar_edges and similar_nodes is None or similar_nodes is None:
            return resultant_subgraph

        resultant_subgraph.nodes = [
            Node(id=node[1], label=node[2], attributes=node[3])
            for node in similar_nodes
        ]

        for node in similar_nodes:
            similar_node = Node(id=node[1], label=node[2], attributes=node[3])
            nodes = atomic(
                all_connected_nodes(similar_node),
                os.getenv("LIBSQL_URL"),
                os.getenv("LIBSQL_AUTH_TOKEN"),
            )

            if not nodes:
                continue

            for i in nodes:
                if i not in resultant_subgraph.nodes:
                    resultant_subgraph.nodes.append(i)

        resultant_subgraph.edges = [
            Edge(source=edge[1], target=edge[2], label=edge[3], attributes=edge[4])
            for edge in similar_edges
        ]
        for edge in similar_edges:
            similar_edge = Edge(
                source=edge[1],
                target=edge[2],
                label=edge[3],
                attributes=edge[4],
            )
            nodes = atomic(
                all_connected_nodes(similar_edge),
                os.getenv("LIBSQL_URL"),
                os.getenv("LIBSQL_AUTH_TOKEN"),
            )

            if not nodes:
                continue

            for node in nodes:
                if node not in resultant_subgraph.nodes:
                    resultant_subgraph.nodes.append(node)

    except KeyError:
        return KnowledgeGraph()

    return resultant_subgraph
