# About

This is the [PyPI](https://pypi.org/) package of the [simple-graph](https://github.com/dpapathanasiou/simple-graph/blob/main/python) implementation in [Python](https://www.python.org/), which is a simple [graph database](https://en.wikipedia.org/wiki/Graph_database) in [SQLite](https://www.sqlite.org/), inspired by "[SQLite as a document database](https://dgl.cx/2020/06/sqlite-json-support)".

## Build and Test

How to [generate the distribution archive](https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives) and confirm it on [test.pypi.org](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives), also based on the [pypa/sampleproject](https://github.com/pypa/sampleproject):

```sh
rm -rf build dist src/simple_graph_sqlite.egg-info
python -m build
python -m twine upload --repository testpypi dist/*
```

Create a virtual environment for the test package, activate it, pull from [test.pypi.org](https://test.pypi.org) (the `--extra-index-url` is necessary since the `graphviz` and/or `Jinja2` dependencies may not be in the test archive), and confirm the package is available:

```sh
$ pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple simple-graph-sqlite graphviz==0.16 Jinja2==3.1.2
$ python
Python 3.6.13 |Anaconda, Inc.| (default, Jun  4 2021, 14:25:59) 
[GCC 7.5.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from simple_graph_sqlite import database as db
```

With the test package installed, update `PYTHONPATH` to include `./tests` and run `pytest` from the root of this repository. If the tests pass, rebuild and push to [pypi.org](https://pypi.org):

```sh
rm -rf build dist src/simple_graph_sqlite.egg-info
python -m build
python -m twine upload --repository pypi dist/*
```

# Structure

The [schema](https://github.com/dpapathanasiou/simple-graph/tree/main/sql/schema.sql) consists of just two structures:

* Nodes - these are any [json](https://www.json.org/) objects, with the only constraint being that they each contain a unique `id` value
* Edges - these are pairs of node `id` values, specifying the direction, with an optional json object as connection properties

There are also traversal functions as native SQLite [Common Table Expressions](https://www.sqlite.org/lang_with.html):

* [Both directions](https://github.com/dpapathanasiou/simple-graph/tree/main/sql/traverse.sql)
* [Inbound](https://github.com/dpapathanasiou/simple-graph/tree/main/sql/traverse-inbound.sql)
* [Outbound](https://github.com/dpapathanasiou/simple-graph/tree/main/sql/traverse-outbound.sql)

# Applications

* [Social networks](https://en.wikipedia.org/wiki/Social_graph)
* [Interest maps/recommendation finders](https://en.wikipedia.org/wiki/Interest_graph)
* [To-do / task lists](https://en.wikipedia.org/wiki/Task_list)
* [Bug trackers](https://en.wikipedia.org/wiki/Open-source_software_development#Bug_trackers_and_task_lists)
* [Customer relationship management (CRM)](https://en.wikipedia.org/wiki/Customer_relationship_management)
* [Gantt chart](https://en.wikipedia.org/wiki/Gantt_chart)

# Usage

## Installation Requirements

* [SQLite](https://www.sqlite.org/), version 3.31.0 or higher; get the latest source or precompiled binaries from the [SQLite Download Page](https://www.sqlite.org/download.html)
* [Graphviz](https://graphviz.org/) for visualization ([download page](https://www.graphviz.org/download/), [installation procedure for Windows](https://forum.graphviz.org/t/new-simplified-installation-procedure-on-windows/224))
* [Jinja2](https://pypi.org/project/Jinja2/) for the search and traversal templates

## Basic Functions

The [database script](src/simple_graph_sqlite/database.py) provides convenience functions for [atomic transactions](https://en.wikipedia.org/wiki/Atomicity_(database_systems)) to add, delete, connect, and search for nodes.

Any single node or path of nodes can also be depicted graphically by using the `visualize` function within the database script to generate [dot](https://graphviz.org/doc/info/lang.html) files, which in turn can be converted to images with Graphviz.

### Example

Dropping into a python shell, we can create, [upsert](https://en.wiktionary.org/wiki/upsert), and connect people from the early days of [Apple Computer](https://en.wikipedia.org/wiki/Apple_Inc.). The resulting database will be saved to a SQLite file named `apple.sqlite`:

```
>>> apple = "apple.sqlite"
>>> from simple_graph_sqlite import database as db
>>> db.initialize(apple)
>>> db.atomic(apple, db.add_node({'name': 'Apple Computer Company', 'type':['company', 'start-up'], 'founded': 'April 1, 1976'}, 1))
>>> db.atomic(apple, db.add_node({'name': 'Steve Wozniak', 'type':['person','engineer','founder']}, 2))
>>> db.atomic(apple, db.add_node({'name': 'Steve Jobs', 'type':['person','designer','founder']}, 3))
>>> db.atomic(apple, db.add_node({'name': 'Ronald Wayne', 'type':['person','administrator','founder']}, 4))
>>> db.atomic(apple, db.add_node({'name': 'Mike Markkula', 'type':['person','investor']}, 5))
>>> db.atomic(apple, db.connect_nodes(2, 1, {'action': 'founded'}))
>>> db.atomic(apple, db.connect_nodes(3, 1, {'action': 'founded'}))
>>> db.atomic(apple, db.connect_nodes(4, 1, {'action': 'founded'}))
>>> db.atomic(apple, db.connect_nodes(5, 1, {'action': 'invested', 'equity': 80000, 'debt': 170000}))
>>> db.atomic(apple, db.connect_nodes(1, 4, {'action': 'divested', 'amount': 800, 'date': 'April 12, 1976'}))
>>> db.atomic(apple, db.connect_nodes(2, 3))
>>> db.atomic(apple, db.upsert_node(2, {'nickname': 'Woz'}))
```

There are also bulk operations, to insert and connect lists of nodes in one transaction.

The nodes can be searched by their ids:

```
>>> db.atomic(apple, db.find_node(1))
{'name': 'Apple Computer Company', 'type': ['company', 'start-up'], 'founded': 'April 1, 1976', 'id': 1}
```

Searches can also use combinations of other attributes, both as strict equality, or using `LIKE` in combination with a trailing `%` for "starts with" or `%` at both ends for "contains":

```
>>> db.atomic(apple, db.find_nodes([db._generate_clause('name', predicate='LIKE')], ('Steve%',)))
[{'name': 'Steve Wozniak', 'type': ['person', 'engineer', 'founder'], 'id': 2, 'nickname': 'Woz'}, {'name': 'Steve Jobs', 'type': ['person', 'designer', 'founder'], 'id': 3}]
>>> db.atomic(apple, db.find_nodes([db._generate_clause('name', predicate='LIKE'), db._generate_clause('name', predicate='LIKE', joiner='OR')], ('%Woz%', '%Markkula',)))
[{'name': 'Steve Wozniak', 'type': ['person', 'engineer', 'founder'], 'id': 2, 'nickname': 'Woz'}, {'name': 'Mike Markkula', 'type': ['person', 'investor'], 'id': 5}]
```

More complex queries to introspect the json body, using the [sqlite json_tree() function](https://www.sqlite.org/json1.html), are also possible, such as this query for every node whose `type` array contains the value `founder`:

```
>>> db.atomic(apple, db.find_nodes([db._generate_clause('type', tree=True)], ('founder',), tree_query=True, key='type'))
[{'name': 'Steve Wozniak', 'type': ['person', 'engineer', 'founder'], 'id': 2, 'nickname': 'Woz'}, {'name': 'Steve Jobs', 'type': ['person', 'designer', 'founder'], 'id': 3}, {'name': 'Ronald Wayne', 'type': ['person', 'administrator', 'founder'], 'id': 4}]
```

See the `_generate_clause()` and `_generate_query()` functions in [database.py](src/simple_graph_sqlite/database.py) for usage hints.

Paths through the graph can be discovered with a starting node id, and an optional ending id; the default neighbor expansion is nodes connected nodes in either direction, but that can changed by specifying either `find_outbound_neighbors` or `find_inbound_neighbors` instead:

```
>>> db.traverse(apple, 2, 3)
['2', '1', '3']
>>> db.traverse(apple, 4, 5)
['4', '1', '2', '3', '5']
>>> db.traverse(apple, 5, neighbors_fn=db.find_inbound_neighbors)
['5']
>>> db.traverse(apple, 5, neighbors_fn=db.find_outbound_neighbors)
['5', '1', '4']
>>> db.traverse(apple, 5, neighbors_fn=db.find_neighbors)
['5', '1', '2', '3', '4']
```

Any path or list of nodes can rendered graphically by using the `visualize` function. This command produces [dot](https://graphviz.org/doc/info/lang.html) files, which are also rendered as images with Graphviz:

```
>>> from visualizers import graphviz_visualize
>>> graphviz_visualize(apple, 'apple.dot', [4, 1, 5])
```

The [resulting text file](tests/fixtures/apple-raw.dot) also comes with an associated image (the default is [png](https://en.wikipedia.org/wiki/Portable_Network_Graphics), but that can be changed by supplying a different value to the `format` parameter)

The default options include every key/value pair (excluding the id) in the node and edge objects, and there are display options to help refine what is produced:

```
>>> graphviz_visualize(apple, 'apple.dot', [4, 1, 5], exclude_node_keys=['type'], hide_edge_key=True)
```

The [resulting dot file](tests/fixtures/apple.dot) can be edited further as needed; the [dot guide](https://graphviz.org/pdf/dotguide.pdf) has more options and examples.