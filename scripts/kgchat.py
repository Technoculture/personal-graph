import os
import sys
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from personal_graph.graph import Graph
from dotenv import load_dotenv

load_dotenv()

with Graph(
    db_url=os.getenv("LIBSQL_URL"), auth_token=os.getenv("LIBSQL_AUTH_TOKEN")
) as kg:
    st.title("Conversational Knowledge Graph")

    # Create two columns for chat and graph visualization
    col1, col2 = st.columns(2)

    with col1:
        chat_history = st.empty()

        # Start the conversation in curious mode
        st.write(
            "Hello! I'm an AI assistant, and I'm curious to learn more about you. Let's start a conversation!"
        )
        user_input = st.text_input("You: ", key="user_input")

        # Process the user input and update the knowledge graph
        kg_response = kg.insert(user_input)

        chat_history.markdown(f"You: {user_input}")

        with col2:
            graph_viz_source = kg.visualize("sample.dot", kg.fetch_ids_from_db())
            if graph_viz_source:
                graph_viz = st.graphviz_chart(graph_viz_source)
            else:
                st.warning("No knowledge graph to visualize.")
