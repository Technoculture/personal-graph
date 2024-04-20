# Personal-Graph: Graph for building memory for AI applications
[![PyPI version](https://badge.fury.io/py/personal-graph.svg)](https://badge.fury.io/py/personal-graph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Checks and Test](https://github.com/Technoculture/personal-graph/actions/workflows/personal-graph.yaml/badge.svg)](https://github.com/Technoculture/personal-graph/actions/workflows/personal-graph.yaml)

Personal-Graph is a Python library for creating, managing, and querying knowledge graphs. It aims to help solve working and long-term memory challenges in AI systems, particularly Large Language Models (LLMs).

## Features
- 🚀 **Can Be Fast**: Built on libsql, a high-performance SQLite engine in Rust
- 👨 **One DB per User**: Integrate with Turso DB for private, user-specific knowledge graphs
- 💬 **Natural Language Interfaces**: Natural language queries powered by Sqlite-vss and Instructor
- 🤖 **ML-Ready**: Export data for machine learning libraries like Networkx and PyG

## Installation

Install Personal-Graph using pip:
```sh
pip install personal-graph
```

## Usage

### Building a Working Memory for an AI

```python
from personal_graph import Graph

graph = Graph("your_db_url", "your_auth_token")

# Insert information into the graph
graph.insert(text="Alice is Bob's sister. Bob works at Google.")

# Retrieve relevant information from the graph
query = "Who is Alice?"
results = graph.search(query)

# Use the retrieved information to answer questions
print(f"Question: {query}")
print(f"Answer: Alice is Bob's sister.")

query = "Where does Bob work?"
results = graph.search(query)
print(f"Question: {query}")
print(f"Answer: Bob works at Google.")
```

In this example, we insert information about Alice and Bob into the knowledge graph. We then use the search method to retrieve relevant information based on the given queries. The retrieved information can be used as part of the AI's working memory to answer questions and provide context for further interactions.

### Building Long-Term Memory
```python
from personal_graph import Graph

graph = Graph("your_db_url", "your_auth_token")

# Insert information about conversations with the user over time
graph.insert(
  text="User talked about their childhood dreams and aspirations.",
  attributes={
    "date": "2023-01-15",
    "topic": "childhood dreams",
    "depth_score": 3
  })

graph.insert(
  text="User discussed their fears and insecurities in their current relationship.",
  attributes={
    "date": "2023-02-28",
    "topic": "relationship fears",
    "depth_score": 4
})

graph.insert(
  text="User shared their spiritual beliefs and existential questions.",
  attributes={
    "date": "2023-03-10",
    "topic": "spirituality and existence",
    "depth_score": 5
})

graph.insert(
  text="User mentioned their favorite hobbies and weekend activities.",
  attributes={
    "date": "2023-04-02",
    "topic": "hobbies",
    "depth_score": 2
})

# User queries about the deepest conversation
query = "What was the deepest conversation we've ever had?"

results = graph.search(query, sort_by="depth_score", descending=True, limit=1)

if results:
    deepest_conversation = results[0]
    print(f"Question: {query}")
    print(f"Answer: Our deepest conversation was on {deepest_conversation['date']} when we discussed {deepest_conversation['topic']}.")
else:
    print(f"Question: {query}")
    print("Answer: I apologize, but I don't have enough information to determine our deepest conversation.")
```
In this example, we store information about conversations with the user, including the date, topic, and a depth score. The depth score represents how meaningful the conversation was.

When the user asks about the deepest conversation, we search for the conversation with the highest depth score using the search method. We sort the results by the depth score in descending order and limit the output to one conversation.

If a conversation is found, the AI responds with the date and topic of the deepest conversation. If no conversations are found, the AI informs the user that it doesn't have enough information.

This example demonstrates how Personal-Graph can be used to build long-term memory about user interactions and retrieve specific information based on criteria like conversation depth.

### Creating and Querying a Knowledge Graph
```py
from personal_graph import Graph, natural

graph = Graph("your_db_url", "your_auth_token")

nl_query = "Increased thirst, weight loss, increased hunger, and frequent urination are all symptoms of diabetes."
graph = natural.insert(text=nl_query)

search_query = "I am losing weight too frequently."
knowledge_graph = natural.search_from_graph(search_query)

print(knowledge_graph)
```

### Retrieval and Question-Answering
```py
import dspy
from personal_graph.graph import Graph
from personal_graph.retriever import PersonalRM

graph = Graph("your_db_url", "your_auth_token")
retriever = PersonalRM(graph=graph, k=2)

class RAG(dspy.Module):
    def __init__(self, depth=3):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=depth)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)

    def forward(self, question):
        context = self.retrieve(question).passages
        prediction = self.generate_answer(context=context, question=question)
        return dspy.Prediction(context=context, answer=prediction.answer)

rag = RAG(depth=2)
answer = rag("How is Jack related to James?")
print(answer)
```

For more details and API documentation, see the Personal-Graph Documentation.

## Contributing
Contributions are welcome! Please read our Contribution Guidelines and Code of Conduct.

## License
Personal-Graph is released under the MIT License.

## Contact
Questions, feedback, or suggestions? Reach out at satyam@technoculture.io or open an issue on GitHub.
