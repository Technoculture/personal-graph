"""
Use models.py and Instructor to provide a natural language interface to the graph db
"""

import os
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
from models import KnowledgeGraph  # type: ignore

load_dotenv()
client = instructor.patch(OpenAI(api_key=os.getenv("OPEN_API_KEY")))

app = FastAPI()


@app.get("/graph/insert", response_model=KnowledgeGraph)
async def graph_insert(query: str):
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
    return kg
