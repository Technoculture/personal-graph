# Libsql-graph-db

> This repo add functionality on top of the simple graph db [simple-graph-pypi](https://github.com/dpapathanasiou/simple-graph-pypi) in order to support libsql instead of sqlite, and to add AI native features such as similarity search and Natural language interface.

1. Modern Interface
Some amounts of JSON validation and Context Manager/Class wrapper
  ```py
  # the interface would look like something like this
  with lgdb.connect(url, token) as graph:
    graph.add_node(Node(name="", id=1, attributes={...}))
    graph.add_node(Node(name="", id=2, attributes={...}))
    graph.connect(1, 2, relation={...})
  ```
2. AI Native Features
     - Semantic Search (Sqlite-vss)
     - Natural language interface to KGs (Instructor, Pydantic)
3. Good Performance on reads (even with complex queries)
     - Local replicas are supported by libsql
4. Support for Machine Learning Libraries
     - Export to dict functions for Networkx/PyG etc 

## Time Complexity

| Scenario | Average Time Complexity | Worst Case Time Complexity |
| -------- | ----------------------- | -------------------------- |
| Single Node Insert | O(1) | O(1) |
| Single Edge Insert | O(1) | O(1) |
| Single Node Retrieval by ID | O(1) | O(1) |
| Single Edge Retrieval by ID | O(1) | O(1) |
| Retrieval of All Nodes | O(n) | O(n) |
| Retrieval of All Edges | O(m) | O(m) |
| Retrieval of All Neighbors of a Node	O(avg_degree) | O(n) |
| Retrieval of All Edges of a Node	O(avg_degree) | O(n) | 
| BFS/DFS Traversal | O(n + m) | O(n + m) |
| Shortest Path (Unweighted) | O(n + m) | O(n + m) |
| Shortest Path (Weighted) | O((n + m) log n) | O((n + m) log n) |
| Connected Components | O(n + m) | O(n + m) |
| Strongly Connected Components | O(n + m) | O(n + m) |
| Minimum Spanning Tree | O(m log n) | O(m log n) |
| Semantic Search (Approximate) | O(log n) | O(n) |
| Natural Language Query (Approximate) | O(n) | O(n^2) |

## Usage

### Basic Functions

The [database script](libsql_graph_db/database.py) provides convenience functions for [atomic transactions](https://en.wikipedia.org/wiki/Atomicity_(database_systems)) to add, delete, connect, and search for nodes.

Any single node or path of nodes can also be depicted graphically by using the `visualize` function within the database script to generate [dot](https://graphviz.org/doc/info/lang.html) files, which in turn can be converted to images with Graphviz.

#### Example

It needs database url(db_url) and authentication token(auth_token) to connect with a remote database:

```
>>> from libsql_graph_db import database as db
>>> db.initialize(db_url, auth_token)
>>> db.atomic(db_url, auth_token, db.add_node({'name': 'Apple Computer Company', 'type':['company', 'start-up'], 'founded': 'April 1, 1976'}, 1))
>>> db.atomic(db_url, auth_token, db.add_node({'name': 'Steve Wozniak', 'type':['person','engineer','founder']}, 2))
>>> db.atomic(db_url, auth_token, db.add_node({'name': 'Steve Jobs', 'type':['person','designer','founder']}, 3))
>>> db.atomic(db_url, auth_token, db.add_node({'name': 'Ronald Wayne', 'type':['person','administrator','founder']}, 4))
>>> db.atomic(db_url, auth_token, db.add_node({'name': 'Mike Markkula', 'type':['person','investor']}, 5))
>>> db.atomic(db_url, auth_token, db.connect_nodes(2, 1, {'action': 'founded'}))
>>> db.atomic(db_url, auth_token, db.connect_nodes(3, 1, {'action': 'founded'}))
>>> db.atomic(db_url, auth_token, db.connect_nodes(4, 1, {'action': 'founded'}))
>>> db.atomic(db_url, auth_token, db.connect_nodes(5, 1, {'action': 'invested', 'equity': 80000, 'debt': 170000}))
>>> db.atomic(db_url, auth_token, db.connect_nodes(1, 4, {'action': 'divested', 'amount': 800, 'date': 'April 12, 1976'}))
>>> db.atomic(db_url, auth_token,  db.connect_nodes(2, 3))
>>> db.atomic(db_url, auth_token, db.upsert_node(2, {'nickname': 'Woz'}))
```

There are also bulk operations, to insert and connect lists of nodes in one transaction.

The nodes can be searched by their ids:

```
>>> db.atomic(db_url, auth_token, db.find_node(1))
{'name': 'Apple Computer Company', 'type': ['company', 'start-up'], 'founded': 'April 1, 1976', 'id': 1}
```

Searches can also use combinations of other attributes, both as strict equality, or using `LIKE` in combination with a trailing `%` for "starts with" or `%` at both ends for "contains":

```
>>> db.atomic(db_url, auth_token, db.find_nodes([db._generate_clause('name', predicate='LIKE')], ('Steve%',)))
[{'name': 'Steve Wozniak', 'type': ['person', 'engineer', 'founder'], 'id': 2, 'nickname': 'Woz'}, {'name': 'Steve Jobs', 'type': ['person', 'designer', 'founder'], 'id': 3}]
>>> db.atomic(db_url, auth_token, db.find_nodes([db._generate_clause('name', predicate='LIKE'), db._generate_clause('name', predicate='LIKE', joiner='OR')], ('%Woz%', '%Markkula',)))
[{'name': 'Steve Wozniak', 'type': ['person', 'engineer', 'founder'], 'id': 2, 'nickname': 'Woz'}, {'name': 'Mike Markkula', 'type': ['person', 'investor'], 'id': 5}]
```

More complex queries to introspect the json body, using the [sqlite json_tree() function](https://www.sqlite.org/json1.html), are also possible, such as this query for every node whose `type` array contains the value `founder`:

```
>>> db.atomic(db_url, auth_token,  db.find_nodes([db._generate_clause('type', tree=True)], ('founder',), tree_query=True, key='type'))
[{'name': 'Steve Wozniak', 'type': ['person', 'engineer', 'founder'], 'id': 2, 'nickname': 'Woz'}, {'name': 'Steve Jobs', 'type': ['person', 'designer', 'founder'], 'id': 3}, {'name': 'Ronald Wayne', 'type': ['person', 'administrator', 'founder'], 'id': 4}]
```

See the `_generate_clause()` and `_generate_query()` functions in [database.py](libsql_graph_db/database.py) for usage hints.

Paths through the graph can be discovered with a starting node id, and an optional ending id; the default neighbor expansion is nodes connected nodes in either direction, but that can changed by specifying either `find_outbound_neighbors` or `find_inbound_neighbors` instead:

```
>>> db.traverse(db_url, auth_token, 2, 3)
['2', '1', '3']
>>> db.traverse(db_url, auth_token, 4, 5)
['4', '1', '2', '3', '5']
>>> db.traverse(db_url, auth_token, 5, neighbors_fn=db.find_inbound_neighbors)
['5']
>>> db.traverse(db_url, auth_token, 5, neighbors_fn=db.find_outbound_neighbors)
['5', '1', '4']
>>> db.traverse(db_url, auth_token, 5, neighbors_fn=db.find_neighbors)
['5', '1', '2', '3', '4']
```

Any path or list of nodes can rendered graphically by using the `visualize` function. This command produces [dot](https://graphviz.org/doc/info/lang.html) files, which are also rendered as images with Graphviz:

```
>>> from visualizers import graphviz_visualize
>>> graphviz_visualize(db_url, auth_token, 'apple.dot', [4, 1, 5])
```

The [resulting text file](tests/fixtures/apple-raw.dot) also comes with an associated image (the default is [png](https://en.wikipedia.org/wiki/Portable_Network_Graphics), but that can be changed by supplying a different value to the `format` parameter)

The default options include every key/value pair (excluding the id) in the node and edge objects, and there are display options to help refine what is produced:

```
>>> graphviz_visualize(db_url, auth_token, 'apple.dot', [4, 1, 5], exclude_node_keys=['type'], hide_edge_key=True)
>>> path_with_bodies = db.traverse(db_url, auth_token, source, target, with_bodies=True) 
>>>graphviz_visualize_bodies('apple.dot', path_with_bodies)
```

The [resulting dot file](tests/fixtures/apple.dot) can be edited further as needed; the [dot guide](https://graphviz.org/pdf/dotguide.pdf) has more options and examples.

## Applications

* [Social networks](https://en.wikipedia.org/wiki/Social_graph)
* [Interest maps/recommendation finders](https://en.wikipedia.org/wiki/Interest_graph)
* [To-do / task lists](https://en.wikipedia.org/wiki/Task_list)
* [Bug trackers](https://en.wikipedia.org/wiki/Open-source_software_development#Bug_trackers_and_task_lists)
* [Customer relationship management (CRM)](https://en.wikipedia.org/wiki/Customer_relationship_management)
* [Gantt chart](https://en.wikipedia.org/wiki/Gantt_chart)
