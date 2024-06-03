from personal_graph import OpenAIClient, KnowledgeGraph
from personal_graph.graph_generator import OpenAITextToGraphParser


def text_to_graph(
    text: str,
    graph_generator: OpenAITextToGraphParser = OpenAITextToGraphParser(
        llm_client=OpenAIClient()
    ),
) -> KnowledgeGraph:
    kg = graph_generator.generate(text)

    return kg
