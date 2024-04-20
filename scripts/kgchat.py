import json
import os
from typing import List
import dspy  # type: ignore
import joblib  # type: ignore
import streamlit as st
from personal_graph.graph import Graph
from personal_graph.models import Node, Edge, KnowledgeGraph
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


def load_cache():
    cache_dir = "cache"
    if (
        os.path.exists(os.path.join(cache_dir, "backstory.pkl"))
        and os.path.exists(os.path.join(cache_dir, "kg.pkl"))
        and os.path.exists(os.path.join(cache_dir, "context.pkl"))
    ):
        backstory = joblib.load(os.path.join(cache_dir, "backstory.pkl"))
        nodes_edges_dict = joblib.load(os.path.join(cache_dir, "kg.pkl"))
        context = joblib.load(os.path.join(cache_dir, "context.pkl"))

        nodes = [Node(**node_dict) for node_dict in nodes_edges_dict["nodes"]]
        edges = [Edge(**edge_dict) for edge_dict in nodes_edges_dict["edges"]]

        kg = KnowledgeGraph(nodes=nodes, edges=edges)

        return backstory, kg, context
    else:
        return None, None, None


def main():
    rag = RAG(depth=2)
    analyzer = MessageAnalyzerModule()

    st.title("Knowledge Graph Chat")

    with Graph(os.getenv("LIBSQL_URL"), os.getenv("LIBSQL_AUTH_TOKEN")) as graph:
        turbo = dspy.OpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPEN_API_KEY"))
        cached_backstory, cached_kg, cached_context = load_cache()

        if "initialized" not in st.session_state:
            st.session_state["backstory"] = cached_backstory
            st.session_state["kg"] = cached_kg
            st.session_state["initialized"] = True

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
        backstory = stx.scrollableTextbox(
            "Enter your backstory", value=st.session_state["backstory"], height=300
        )
    else:
        backstory = st.sidebar.text_area(
            "Enter your backstory", value=st.session_state["backstory"], height=300
        )

    if st.sidebar.button(
        "Load", disabled=st.session_state.get("load_button_disabled", False)
    ):
        st.session_state["load_button_disabled"] = True
        if len(backstory) < 2000:
            st.sidebar.warning("Please enter a backstory with at least 2000 tokens.")
        else:
            kg = graph.insert(backstory)
            st.session_state["kg"] = kg
            st.session_state["backstory"] = backstory
            with st.sidebar.status("Retrieved knowledge graph visualization:"):
                st.sidebar.graphviz_chart(graph.visualize_graph(kg))

                for idx, context in enumerate(rag(backstory).context, start=1):
                    body = json.loads(context).get("body", "")
                    st.sidebar.write(f"{idx}. {body}")
            retriever = PersonalRM(graph=graph, k=2)
            dspy.settings.configure(lm=turbo, rm=retriever)

    if cached_context and cached_kg and "loaded" not in st.session_state:
        st.sidebar.graphviz_chart(graph.visualize_graph(cached_kg))
        for context in cached_context:
            st.sidebar.write(context)
        st.session_state.loaded = True

    if prompt := st.chat_input("Say Something?"):
        kg = st.session_state["kg"]
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
                is_unique = graph.is_unique_prompt(prompt, 0.6)
                if is_unique and kg:
                    sub_graph = graph.insert(prompt)
                    for sg_node in sub_graph.nodes:
                        kg.nodes.append(sg_node)

                    for sg_edge in sub_graph.edges:
                        kg.edges.append(sg_edge)

                    # Update the backstory with the new prompt
                    st.session_state["backstory"] += "\n" + prompt
                    st.session_state["kg"] = kg

                    # Update the sidebar graph with the new information
                    st.sidebar.graphviz_chart(graph.visualize_graph(kg))
                    for idx, context in enumerate(
                        rag(st.session_state.backstory).context, start=1
                    ):
                        body = json.loads(context).get("body", "")
                        st.sidebar.write(f"{idx}. {body}")
                    st.graphviz_chart(graph.visualize_graph(sub_graph))

                else:
                    sub_graph = graph.search_query(prompt)
                    st.graphviz_chart(graph.visualize_graph(sub_graph))

            st.markdown(response.answer)

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append(
            {"role": "assistant", "content": response.answer}
        )


if __name__ == "__main__":
    main()
