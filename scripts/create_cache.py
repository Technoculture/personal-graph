import os
import json
import dspy  # type: ignore
import joblib  # type: ignore
from personal_graph.graph import Graph
from personal_graph.retriever import PersonalRM

DEFAULT_BACKSTORY = ""


class GenerateAnswer(dspy.Signature):
    """Answer questions with short factoid answers."""

    context = dspy.InputField(desc="may contain relevant facts from user's graph")
    question = dspy.InputField()
    answer = dspy.OutputField(
        desc="a short answer to the question, deduced from the information found in the user's graph"
    )


class RAG(dspy.Module):
    def __init__(self, depth=3):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=depth)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)

    def forward(self, question):
        context = self.retrieve(question).passages
        prediction = self.generate_answer(context=context, question=question)
        return dspy.Prediction(context=context, answer=prediction.answer)


def create_and_save_cache(rag):
    list_of_context = []

    with Graph(os.getenv("LIBSQL_URL"), os.getenv("LIBSQL_AUTH_TOKEN")) as graph:
        turbo = dspy.OpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPEN_API_KEY"))

        kg = graph.insert(DEFAULT_BACKSTORY)
        retriever = PersonalRM(graph=graph, k=2)
        dspy.settings.configure(lm=turbo, rm=retriever)

        # Convert KnowledgeGraph object to a dictionary
        nodes_edges_dict = {
            "nodes": [node.__dict__ for node in kg.nodes],
            "edges": [edge.__dict__ for edge in kg.edges],
        }

        for idx, context in enumerate(rag(DEFAULT_BACKSTORY).context, start=1):
            body = json.loads(context).get("body", "")
            list_of_context.append(f"{idx}. {body}")

    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    joblib.dump(DEFAULT_BACKSTORY, os.path.join(cache_dir, "backstory.pkl"))
    joblib.dump(nodes_edges_dict, os.path.join(cache_dir, "kg.pkl"))
    joblib.dump(list_of_context, os.path.join(cache_dir, "context.pkl"))


def main(rag):
    """
    This script will create  the cache with default backstory and knowledge graph
    """
    create_and_save_cache(rag)


if __name__ == "__main__":
    rag = RAG(depth=2)
    main(rag)
