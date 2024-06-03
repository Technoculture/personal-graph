from personal_graph import (
    KnowledgeGraph as KnowledgeGraph,
    OpenAIClient as OpenAIClient,
)
from personal_graph.graph_generator import (
    OpenAITextToGraphParser as OpenAITextToGraphParser,
)

def text_to_graph(
    text: str, graph_generator: OpenAITextToGraphParser = ...
) -> KnowledgeGraph: ...
