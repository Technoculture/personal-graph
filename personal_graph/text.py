from typing import Union

from personal_graph import OpenAIClient, KnowledgeGraph
from personal_graph.graph_generator import (
    OpenAITextToGraphParser,
    OllamaTextToGraphParser,
)


def text_to_graph(
    text: str,
    graph_generator: Union[
        OpenAITextToGraphParser, OllamaTextToGraphParser
    ] = OpenAITextToGraphParser(llm_client=OpenAIClient()),
) -> KnowledgeGraph:
    kg = graph_generator.generate(text)

    return kg
