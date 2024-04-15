import os
import dspy  # type: ignore
import streamlit as st
from personal_graph.graph import Graph
from personal_graph.retriever import PersonalRM

turbo = dspy.OpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPEN_API_KEY"))
retriever = PersonalRM(
    db_url=os.getenv("LIBSQL_URL"), auth_token=os.getenv("LIBSQL_AUTH_TOKEN"), k=2
)

dspy.settings.configure(lm=turbo, rm=retriever)


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


def main():
    rag = RAG(depth=2)
    st.title("Knowledge Graph Chat")

    graph = Graph(os.getenv("LIBSQL_URL"), os.getenv("LIBSQL_AUTH_TOKEN"))

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.sidebar.title("Backstory")
    backstory = st.sidebar.text_input("Enter your backstory")

    if st.sidebar.button("Load"):
        kg = graph.insert(backstory)
        st.sidebar.graphviz_chart(graph.visualize_graph(kg))

    if prompt := st.chat_input("Say Something?"):
        with st.chat_message("user"):
            response = rag(prompt)

            st.markdown(response.answer)


if __name__ == "__main__":
    main()
