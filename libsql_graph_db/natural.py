import os
import instructor
import uuid
from openai import OpenAI
from dotenv import load_dotenv
from models import KnowledgeGraph  # type: ignore
from database import initialize, add_node, atomic, connect_nodes  # type: ignore

load_dotenv()
client = instructor.patch(OpenAI(api_key=os.getenv("OPEN_API_KEY")))
db_url = os.getenv("LIBSQL_URL")
auth_token = os.getenv("LIBSQL_AUTH_TOKEN")


def insert_into_graph(query: str) -> KnowledgeGraph:
    initialize(db_url, auth_token)

    kg = client.chat.completions.create(
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

    uuid_dict = {}

    for node in kg.nodes:
        uuid_dict[node.id] = str(uuid.uuid4())
        atomic(
            add_node({"body": node.body, "label": node.label}, uuid_dict[node.id]),
            db_url,
            auth_token,
        )

    for edge in kg.edges:
        atomic(
            connect_nodes(
                uuid_dict[edge.source],
                uuid_dict[edge.target],
                {"properties": edge.label},
            ),
            db_url,
            auth_token,
        )

    return kg
