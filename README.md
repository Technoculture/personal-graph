# Personal-Graph: Graph for building memory for AI applications
[![PyPI version](https://badge.fury.io/py/personal-graph.svg)](https://badge.fury.io/py/personal-graph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Checks and Test](https://github.com/Technoculture/personal-graph/actions/workflows/personal-graph.yaml/badge.svg)](https://github.com/Technoculture/personal-graph/actions/workflows/personal-graph.yaml)


[![](https://dcbadge.limes.pink/api/server/https://discord.gg/YPJCBwy5M6)](https://discord.gg/YPJCBwy5M6)

Personal-Graph is a Python library for creating, managing, and querying knowledge graphs. It aims to help solve working and long-term memory challenges in AI systems, particularly Large Language Models (LLMs).

## Features
- 🚀 **Can Be Fast**: Built on libsql, a high-performance SQLite engine in Rust
- 👨 **One DB per User**: Integrate with Turso DB for private, user-specific knowledge graphs
- 💬 **Natural Language Interfaces**: Natural language queries powered by Sqlite-vss and Instructor
- 🤖 **ML-Ready**: Export data for machine learning libraries like Networkx and PyG
- ✅ Supports local execution with Ollama LLMs and Embedding Models
- ✅ Supports local db for both storing graph and embeddings

## WIP
- Adding support for Columnar Database: DuckDB
- Implementing Graph Neural Network Algorithms: TransE, TransE, Query2Box

## Installation

Install Personal-Graph using pip:
```sh
pip install personal-graph
```

## Usage

### Building a Working Memory for an AI

```python
from personal_graph import GraphDB
from personal_graph.text import text_to_graph
from personal_graph.vector_store import VliteVSS

vector_store = VliteVSS(collection="memories")
graph = GraphDB(vector_store=vector_store)

# Insert information into the graph
g = text_to_graph("Alice is Bob's sister. Bob works at Google.")
graph.insert_graph(g)

# Retrieve relevant information from the graph
query = "Who is Alice?"
results = graph.search(query)
print(results)

# Use the retrieved information to answer questions
print(f"Question: {query}")
print(f"Answer: Alice is Bob's sister.")

query = "Where does Bob work?"
results = graph.search(query)
print(results)
print(f"Question: {query}")
print(f"Answer: Bob works at Google.")
```

In this example, we insert information about Alice and Bob into the knowledge graph. We then use the search method to retrieve relevant information based on the given queries. The retrieved information can be used as part of the AI's working memory to answer questions and provide context for further interactions.

### Building Long-Term Memory
```python
from personal_graph import GraphDB
from personal_graph.vector_store import VliteVSS

vector_store = VliteVSS(collection="memories")
graph = GraphDB(vector_store=vector_store)

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

deepest_conversation = graph.search(query, sort_by="depth_score", descending=True, limit=1)
```
In this example, we store information about conversations with the user, including the date, topic, and a depth score. The depth score represents how meaningful the conversation was.

When the user asks about the deepest conversation, we search for the conversation with the highest depth score using the search method. We sort the results by the depth score in descending order and limit the output to one conversation.

If a conversation is found, the AI responds with the date and topic of the deepest conversation. If no conversations are found, the AI informs the user that it doesn't have enough information.

This example demonstrates how Personal-Graph can be used to build long-term memory about user interactions and retrieve specific information based on criteria like conversation depth.

### Creating and Querying a Knowledge Graph
```py
from personal_graph import GraphDB
from personal_graph.text import text_to_graph
from personal_graph.vector_store import VliteVSS

vector_store = VliteVSS(collection="memories")

graphdb = GraphDB(vector_store=vector_store)

nl_query = "Increased thirst, weight loss, increased hunger, and frequent urination are all symptoms of diabetes."
kg = text_to_graph(text=nl_query)
graphdb.insert_graph(kg)

search_query = "I am losing weight too frequently."
g = text_to_graph(search_query)
print(g)

graphdb.insert_graph(g)
```

### Retrieval and Question-Answering
```py
import os
import dspy
from personal_graph import GraphDB, PersonalRM

db = GraphDB() # storage_db is in-memory sqlite, vector_db is in vlite
turbo = dspy.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
retriever = PersonalRM(graph=db, k=2)
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

rag = RAG(depth=2)
response = rag("How is Jack related to James?")
print(response.answer)
```

### Local Usage

```py
from personal_graph.graph import GraphDB
from personal_graph.graph_generator import OllamaTextToGraphParser
from personal_graph.database import SQLite
from personal_graph.vector_store import VliteVSS
from personal_graph.clients import OllamaClient, OllamaEmbeddingClient

phi3 = OllamaClient(model_name="phi3")
nomic_embed = OllamaEmbeddingClient(model_name="nomic-embed-text")

storage_db = SQLite(local_path="./local.db")
vector_store = VliteVSS(collection="./vectors")

graph_generator=OllamaTextToGraphParser(llm_client=phi3)
print(graph_generator) # Should print the InstructorGraphGenerator 

with GraphDB(
    database=storage_db, 
    vector_store=vector_store, 
    graph_generator=graph_generator
  ) as db:
    print(db)
```

### PersonalGraph to PyG, then back to PersonalGraph
The following is just a sketch of the planned flow. WIP.

```py
graphdb = GraphDB(storage=db, vector_store=vector_store, graph_generator=graph_generator)

graphdb.load_dataset("KarateClub")

pyg_graph = graphdb.to_pyg()

updated_graph = model(pyg_graph) # Run Neural Network algorithms here using PyG

graphdb.from_pyg(updated_graph)
```

## Video Description
This video best describes the personal graph library.
[[!personal graph]](https://www.loom.com/share/6c715563b8ec45f280213e5466f0be14)

For more details and API documentation, see the Personal-Graph Documentation.

## Contributing
Contributions are welcome! Feel free to create issues for BUGs and feature requests.

## License
Personal-Graph is released under the MIT License.

## Contact
Questions, feedback, or suggestions? Reach out at satyam@technoculture.io or open an issue on GitHub.
