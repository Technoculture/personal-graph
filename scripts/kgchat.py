import os
from typing import List, Any

import streamlit as st
from graphviz import Digraph

from personal_graph.graph import Graph
from dotenv import load_dotenv

load_dotenv()


def visualize(filename: str, current_input: str) -> str:
    with Graph(db_url=os.getenv("LIBSQL_URL"), auth_token=os.getenv("LIBSQL_AUTH_TOKEN")) as kg:

        dot = Digraph(comment="Knowledge Graph")

        # Add nodes related to the current input
        nodes = kg.search_query(current_input).nodes
        for node in nodes:
            dot.node(str(node.id), label=f"{node.label}\\n{node.attribute}")

        # Add edges related to the current input
        edges = kg.search_query(current_input).edges
        for edge in edges:
            src_id = str(edge.source)
            tgt_id = str(edge.target)
            dot.edge(src_id, tgt_id, label=edge.label)

        dot.render(filename, view=False)
        return dot.source


# Initialize the knowledge graph
with Graph(db_url=os.getenv("LIBSQL_URL"), auth_token=os.getenv("LIBSQL_AUTH_TOKEN")) as kg:
    st.title("Conversational Knowledge Graph")

    # Create two columns for chat and graph visualization
    col1, col2 = st.columns(2)

    with col1:
        # Chat column
        chat_history = st.empty()

        # Start the conversation in curious mode
        st.write("Hello! I'm an AI assistant, and I'm curious to learn more about you. Let's start a conversation!")
        user_input = st.text_input("You: ", key="user_input")

        # Process the user input and update the knowledge graph
        kg_response = kg.insert(user_input)

        chat_history.markdown(f"You: {user_input}")
        # chat_history.markdown(f"AI: {response}")

        # Update the knowledge graph visualization
        with col2:
            graph_viz_source = visualize("sample.dot", user_input)
            if graph_viz_source:
                graph_viz = st.graphviz_chart(graph_viz_source)
            else:
                st.warning("No knowledge graph to visualize.")