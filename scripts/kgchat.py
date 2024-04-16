import json
import os
from typing import List
import dspy  # type: ignore
import streamlit as st
from personal_graph.graph import Graph
from personal_graph.retriever import PersonalRM

try:
    import streamlit_scrollable_textbox as stx  # type: ignore
except ImportError:
    stx = None


class UserMessageAnalyzer(dspy.Signature):
    new_message: str = dspy.InputField(desc="A new message by the user")
    structured_message: List[str] = dspy.OutputField(
        desc="Message understood in terms of the underlying intent and objective"
    )


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


class MessageAnalyzerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyze_message = dspy.ChainOfThought(UserMessageAnalyzer)

    def forward(self, new_message):
        return self.analyze_message(new_message=new_message)


def main():
    rag = RAG(depth=2)
    analyzer = MessageAnalyzerModule()

    st.title("Knowledge Graph Chat")

    graph = Graph(os.getenv("LIBSQL_URL"), os.getenv("LIBSQL_AUTH_TOKEN"))
    turbo = dspy.OpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPEN_API_KEY"))
    retriever = PersonalRM(graph=graph, k=2)
    dspy.settings.configure(lm=turbo, rm=retriever)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.sidebar.title("Backstory")
    if stx is not None:
        backstory = stx.scrollableTextbox("Enter your backstory", height=300)
    else:
        backstory = st.sidebar.text_area("Enter your backstory", height=300)

    if st.sidebar.button(
        "Load", disabled=st.session_state.get("load_button_disabled", False)
    ):
        st.session_state["load_button_disabled"] = True
        if len(backstory) < 2000:
            st.sidebar.warning("Please enter a backstory with at least 2000 tokens.")
        else:
            kg = graph.insert(backstory)
            with st.sidebar.status("Retrieved knowledge graph visualization:"):
                st.sidebar.graphviz_chart(graph.visualize_graph(kg))

                for idx, context in enumerate(rag(backstory).context, start=1):
                    body = json.loads(context).get("body", "")
                    st.sidebar.write(f"{idx}. {body}")
            retriever = PersonalRM(graph=graph, k=2)
            dspy.settings.configure(lm=turbo, rm=retriever)

    if prompt := st.chat_input("Say Something?"):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status("Understanding User's Message..."):
                structured_message = analyzer(new_message=prompt).structured_message
                st.write(f"- {structured_message}")

            response = rag(prompt)

            with st.status("Retrieving graph and generating response..."):
                contexts = response.context
                for context in contexts:
                    body = json.loads(context).get("body", "")
                    st.write(f"{body}")

            with st.status("Generating response..."):
                kg = graph.search_query(prompt)
                st.graphviz_chart(graph.visualize_graph(kg))

            st.markdown(response.answer)

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append(
            {"role": "assistant", "content": response.answer}
        )


if __name__ == "__main__":
    main()
