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

DEFAULT_BACKSTORY = """
My story begins in the timeless city of Varanasi, where I first opened my eyes to the world on November 15, 1983. The ancient city, with its labyrinthine lanes, majestic ghats, and pervasive spirituality, would indelibly shape my consciousness and worldview. 

I was born into a loving and close-knit family, the second of three children to my parents Aditya and Priya. My father was a professor of history at Banaras Hindu University and my mother a homemaker and community volunteer. From an early age, they instilled in me and my siblings - elder sister Anjali and younger brother Nikhil - a deep love for knowledge and a strong moral compass.

Some of my earliest memories are of our modest but book-crammed home in the Lanka neighborhood, with the gentle chime of temple bells and snatches of devotional songs wafting in the air. I remember snuggling beside my father in his study as he read out stories from the epics, and hovering wide-eyed around my mother in the kitchen as she prepared our favorite treats while regaling us with tales of her own childhood.

I was an energetic and inquisitive child with a ready smile and a love for sports and games. Cricket was my greatest passion and I have sun-drenched memories of playing for hours with my band of neighborhood friends, our shouts and laughter echoing through the alleys. I can still vividly recall the elation of my first half-century in an inter-mohalla tournament when I was 11 and my whole family cheered from the sidelines. 

At the Central Hindu Boys School where I studied, I discovered the joys of learning and the satisfaction of excelling. While I enjoyed all subjects, I had a special affinity for math and science. I have fond memories of beloved teachers like Mr. Shukla who nurtured my curiosity and made complex concepts come alive. I also discovered a love for painting during my school years, losing myself for hours sketching the scenes and characters of my imagination.

Another formative influence was my involvement with the Scouts, which imbued me with a spirit of adventure, service and self-reliance. I relished our camping expeditions to distant forests and mountains where we learned survival skills and forged deep bonds of friendship around flickering bonfires under starlit skies. 

As I grew into adolescence, I became more conscious of the world beyond my immediate milieu. I remember feeling stirred by the biographies of great scientists and thinkers, dreaming that I too might one day unravel the mysteries of the universe and serve humanity through science. At the same time, I was beginning to grapple with the many inequities I observed around me, moved by the plight of the less privileged.

A poignant memory from this time is of a school friend, Raju, the son of a rickshaw puller, who was forced to drop out after 10th standard to support his family. I remember the helpless anguish I felt, glimpsing for the first time the cruelties of circumstance that could stifle dreams and potential. 
"""


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

    with Graph(os.getenv("LIBSQL_URL"), os.getenv("LIBSQL_AUTH_TOKEN")) as graph:
        turbo = dspy.OpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPEN_API_KEY"))

        # Load the default knowledge graph
        if "kg" not in st.session_state and "first" not in st.session_state:
            kg = graph.insert(DEFAULT_BACKSTORY)
            st.session_state["kg"] = kg
            st.session_state.backstory = DEFAULT_BACKSTORY
            st.session_state.first = True
            st.session_state["default_backstory_inserted"] = True

            retriever = PersonalRM(graph=graph, k=2)
            dspy.settings.configure(lm=turbo, rm=retriever)

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
            "Enter your backstory", value=st.session_state.backstory, height=300
        )
    else:
        backstory = st.sidebar.text_area(
            "Enter your backstory", value=st.session_state.backstory, height=300
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

    if st.session_state.first:
        with st.sidebar.status("Retrieved knowledge graph visualization:"):
            st.sidebar.graphviz_chart(graph.visualize_graph(st.session_state["kg"]))

            for idx, context in enumerate(rag(DEFAULT_BACKSTORY).context, start=1):
                body = json.loads(context).get("body", "")
                st.sidebar.write(f"{idx}. {body}")
            st.session_state.first = False

    if prompt := st.chat_input("Say Something?"):
        kg = st.session_state.get("kg", None)
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
                    st.session_state.backstory += "\n" + prompt
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
