# About

This is the [PyPI](https://pypi.org/) package of the [simple-graph](https://github.com/dpapathanasiou/simple-graph/blob/main/python) implementation in [Python](https://www.python.org/), which is a simple [graph database](https://en.wikipedia.org/wiki/Graph_database) in [SQLite](https://www.sqlite.org/), inspired by "[SQLite as a document database](https://dgl.cx/2020/06/sqlite-json-support)".

## Build and Test

How to the [generate distribution archive](https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives) and confirm it on [test.pypi.org](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives):

```sh
rm dist/*
python -m build
python -m twine upload --repository testpypi dist/*
```

Create a virtual environment for the test package, activate it, pull from [test.pypi.org](https://test.pypi.org) (the `--extra-index-url` is necessary since the `graphviz` dependency may not be in the test archive), and confirm the package is available:

```sh
$ pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple simple-graph-sqlite graphviz==0.16
$ python
Python 3.6.13 |Anaconda, Inc.| (default, Jun  4 2021, 14:25:59) 
[GCC 7.5.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from simple_graph_sqlite import database as db
```

With the test package installed, run `pytest` from the root of this repository. If the tests pass, rebuild and push to [pypi.org](https://pypi.org):

```sh
rm dist/*
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

## Basic Functions

The [database script](https://github.com/dpapathanasiou/simple-graph/blob/main/python/database.py) provides convenience functions for [atomic transactions](https://en.wikipedia.org/wiki/Atomicity_(database_systems)) to add, delete, connect, and search for nodes.

Any single node or path of nodes can also be depicted graphically by using the `visualize` function within the database script to generate [dot](https://graphviz.org/doc/info/lang.html) files, which in turn can be converted to images with Graphviz.

See the [documented example](https://github.com/dpapathanasiou/simple-graph/tree/main/python#example) or the [unit tests](https://github.com/dpapathanasiou/simple-graph/blob/main/python/database_test.py) for more.
