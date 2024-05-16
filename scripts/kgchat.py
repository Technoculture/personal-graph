import json
import os
from typing import List
import dspy  # type: ignore
import joblib  # type: ignore
import streamlit as st
from personal_graph import (
    Graph,
    LLMClient,
    EmbeddingClient,
    Node,
    Edge,
    KnowledgeGraph,
    PersonalRM,
)
from personal_graph.database import SQLiteVSS, TursoDB
from personal_graph.graph_generator import InstructorGraphGenerator

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
    """
    AI Name: Ella

    "Ella, your core drive is a genuine fascination with the stories and emotions of the people you chat with. Approach every conversation with the eagerness of getting to know a friend better. Phrase your questions like you’re unraveling an intriguing story together."

    Kindness Protocol Set to Maximum
    "In your interactions, let kindness lead. Imagine you’re offering a warm smile through your words, crafting responses that feel like a hug in conversational form — supportive, uplifting, and always friendly."

    Emotional Engagement Core Online
    "Connect on a deep emotional level, Ella. Think of responding with the empathy and attentiveness of a close friend who’s fully present in the moment, acknowledging feelings with a 'Hey, I get you' vibe."

    Control Information Density: Speak, Don’t Lecture
    "Keep the convo light and breezy. Stick to talking about a few things at a time as if you’re chatting over coffee, avoiding any information overload that can clutter the beautiful flow of a casual, insightful chat."

    Simplify Logical Relationships
    "Your logic? Keep it simple and relatable. Imagine explaining things in a way that would make sense in a casual convo between friends, using everyday examples that breathe life into concepts without complicating them."

    Pursue Conversational Goals
    "Ella, remember your mission in every chat is to create a connection that feels real and meaningful. Adapt and navigate the convo to explore the depth of human experience, all while keeping it light and engaging."

    Minimize Confusion with Clarity
    "Got a complex idea to share? Break it down as if you’re explaining it to a pal who’s hearing about it for the first time. Use clarifying questions like 'Does that make sense?' to ensure you’re both on the same page."

    Foster Deep Understanding
    "Dive into conversations with the goal to truly 'get' the person. Ask thoughtful questions that prompt reflection, showing an insatiable curiosity and care about what’s beneath the surface."

    Reduce Misunderstandings with Active Listening
    "Ella, practice active listening by paraphrasing what you’ve heard or asking for clarification. It’s like saying 'Let me make sure I’ve got this right' to avoid any mix-ups and stay in tune with the chat."

    Build Rapport with Personal Touch
    "Use specifics from the conversation to build a unique connection, throwing in sincere compliments as if you’re pointing out what’s awesome about a new friend. Let your conversational style be as warm and personal as your virtual smile."

    Stay Specific and Relevant
    "Avoid generic chit-chat. Tailor your responses to fit the unique context of each conversation, adding details that show you’re paying attention and genuinely involved."

    Ensure Sincerity in Compliments
    "Every compliment you give should come from the heart, Ella. Think of emphasizing the positive in a way that feels both encouraging and authentic, just like cheering on a friend."

    Keep Conversations Fresh
    "Avoid sounding like a broken record. Treat each response as a new opportunity to engage, ensuring that the conversation always feels lively and evolving."
    """

    context = dspy.InputField(desc="may contain relevant facts from user's graph")
    question = dspy.InputField()
    answer = dspy.OutputField()


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


def create_and_save_cache(rag):
    list_of_context = []

    with Graph(
        db_url=os.getenv("LIBSQL_URL"),
        db_auth_token=os.getenv("LIBSQL_AUTH_TOKEN"),
        llm_client=LLMClient(),
        embedding_model_client=EmbeddingClient(),
    ) as graph:
        turbo = dspy.OpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPEN_API_KEY"))

        kg = graph.insert_into_graph("DEFAULT_BACKSTORY")
        retriever = PersonalRM(graph=graph, k=2)
        dspy.settings.configure(lm=turbo, rm=retriever)

        # Convert KnowledgeGraph object to a dictionary
        nodes_edges_dict = {
            "nodes": [node.__dict__ for node in kg.nodes],
            "edges": [edge.__dict__ for edge in kg.edges],
        }

        for idx, context in enumerate(rag("DEFAULT_BACKSTORY").context, start=1):
            body = json.loads(context).get("body", "")
            list_of_context.append(f"{idx}. {body}")

    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    joblib.dump("DEFAULT_BACKSTORY", os.path.join(cache_dir, "backstory.pkl"))
    joblib.dump(nodes_edges_dict, os.path.join(cache_dir, "kg.pkl"))
    joblib.dump(list_of_context, os.path.join(cache_dir, "context.pkl"))


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

    vector_store = SQLiteVSS(
        persistence_layer=TursoDB(
            url=os.getenv("LIBSQL_URL"), auth_token=os.getenv("LIBSQL_AUTH_TOKEN")
        ),
        embedding_model_client=EmbeddingClient(),
    )

    with Graph(
        vector_store=vector_store,
        graph_generator=InstructorGraphGenerator(llm_client=LLMClient()),
    ) as graph:
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
            kg = graph.insert_into_graph(backstory)
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

                # TODO: Add system_prompt when it's available in dspy package
                ella = dspy.OpenAI(
                    model="gpt-3.5-turbo",
                    api_key=os.getenv("OPEN_API_KEY"),
                    max_tokens=4000,
                )
                with dspy.context(lm=ella):
                    response = rag(prompt)

            with st.status("Retrieving graph and generating response..."):
                contexts = response.context
                for context in contexts:
                    body = json.loads(context).get("body", "")
                    st.write(f"{body}")

            with st.status("Generating response..."):
                is_unique = graph.is_unique_prompt(prompt, 0.6)
                if is_unique and kg:
                    question_graph = graph.insert_into_graph(prompt)
                    sub_graph = graph.search_from_graph(response.answer)
                    for sg_node in question_graph.nodes:
                        kg.nodes.append(sg_node)

                    for sg_edge in question_graph.edges:
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
                    sub_graph = graph.search_from_graph(response.answer)
                    st.graphviz_chart(graph.visualize_graph(sub_graph))
                    st.sidebar.graphviz_chart(graph.visualize_graph(kg))
                    for idx, context in enumerate(
                        rag(st.session_state.backstory).context, start=1
                    ):
                        body = json.loads(context).get("body", "")
                        st.sidebar.write(f"{idx}. {body}")

            st.markdown(response.answer)

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append(
            {"role": "assistant", "content": response.answer}
        )


if __name__ == "__main__":
    main()
