import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from personal_graph.graph import Graph
import os
from examples.dspy_program import RAG

rag = RAG(depth=2)


def main():
    st.title("Knowledge Graph Chat")

    graph = Graph(os.getenv("LIBSQL_URL"), os.getenv("LIBSQL_AUTH_TOKEN"))
    chat_history = []

    st.sidebar.title("Graph Visualization")
    graph_plot = st.sidebar.empty()

    user_input = st.text_input("You: ", key="user_input")
    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        graph.insert(user_input)
        kg = graph.search_query(user_input)

        if kg.nodes:
            graph_plot.graphviz_chart(graph.visualize_graph(kg))
        else:
            graph_plot.warning("No nodes found for the query.")

        response = rag(user_input)
        chat_history.append({"role": "assistant", "content": response.answer})
        for chat in chat_history:
            if chat["role"] == "user":
                st.write("You: " + chat["content"])
            else:
                st.write("Assistant: " + chat["content"])


if __name__ == "__main__":
    main()
