import instructor
from typing import Union
from openai import OpenAI
from abc import ABC, abstractmethod

from personal_graph.models import KnowledgeGraph
from personal_graph.clients import LiteLLMClient, OpenAIClient, OllamaClient


class TextToGraphParserInterface(ABC):
    @abstractmethod
    def generate(self, query: str) -> KnowledgeGraph:
        """Generate a KnowledgeGraph from the given query."""
        pass


class OpenAITextToGraphParser(TextToGraphParserInterface):
    def __init__(
        self,
        llm_client: Union[LiteLLMClient, OpenAIClient],
        system_prompt: str = "You are a high quality knowledge graph generator based on the user query for the purpose of generating descriptive, informative, detailed and accurate knowledge graphs. You can generate proper nodes and edges as a knowledge graph.",
        prompt: str = "Help me describe this user query as a detailed knowledge graph with meaningful relationships that should provide some descriptive attributes(attribute is the detailed and proper information about the edge) and informative labels about the nodes and relationship. Try to make most of the relationships between similar nodes.",
    ):
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.llm_client = llm_client

    def __repr__(self):
        return (
            f"OpenAITextToGraphParser(\n"
            f"    llm_client={self.llm_client},\n"
            f"    system_prompt={self.system_prompt},\n"
            f"    prompt={self.prompt}\n"
            f"  )"
        )

    def generate(self, query: str) -> KnowledgeGraph:
        client = instructor.from_openai(self.llm_client.client)
        knowledge_graph = client.chat.completions.create(
            model=self.llm_client.model_name,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": f"{self.prompt}: {query}",
                },
            ],
            response_model=KnowledgeGraph,
        )
        return knowledge_graph


class OllamaTextToGraphParser(TextToGraphParserInterface):
    def __init__(
        self,
        llm_client: Union[OllamaClient],
        system_prompt: str = "You are a high quality knowledge graph generator based on the user query for the purpose of generating descriptive, informative, detailed and accurate knowledge graphs. You can generate proper nodes and edges as a knowledge graph.",
        prompt: str = "Help me describe this user query as a detailed knowledge graph with meaningful relationships that should provide some descriptive attributes(attributes is the detailed and proper descriptive information about the edges and nodes) and informative labels about the nodes and relationships. Try to make most of the relationships between similar nodes.",
    ):
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.llm_client = llm_client

    def __repr__(self):
        return (
            f"OllamaTextToGraphParser(\n"
            f"    llm_client={self.llm_client},\n"
            f"    system_prompt={self.system_prompt},\n"
            f"    prompt={self.prompt}\n"
            f"  )"
        )

    def generate(self, query: str) -> KnowledgeGraph:
        client = instructor.from_openai(
            OpenAI(
                base_url=self.llm_client.base_url,
                api_key=self.llm_client.api_key,
            ),
            mode=instructor.Mode.JSON,
        )

        knowledge_graph = client.chat.completions.create(
            model=self.llm_client.model_name,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": f"{self.prompt}: {query}",
                },
            ],
            stream=False,
            response_model=KnowledgeGraph,
        )

        return knowledge_graph
