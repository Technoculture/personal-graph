from personal_graph import OpenAILLMClient, KnowledgeGraph
from personal_graph.graph_generator import OpenAITextToGraphParser


def text_to_graph(
    text: str,
    graph_generator: OpenAITextToGraphParser = OpenAITextToGraphParser(
        llm_client=OpenAILLMClient()
    ),
) -> KnowledgeGraph:
    kg = graph_generator.generate(text)

    return kg
