from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
sql = (here / "src" / "simple_graph_sqlite" / "sql")

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='simple-graph-sqlite',
    version='2.1.0',
    description='A simple graph database in SQLite',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dpapathanasiou/simple-graph-pypi',
    author='Denis Papathanasiou',
    packages=['simple_graph_sqlite'],
    package_dir={'simple_graph_sqlite': 'src/simple_graph_sqlite'},
    package_data={
        'simple_graph_sqlite': [f'sql/{file.name}' for file in sql.glob('*')],
    },
    python_requires='>=3.6, <4',
    install_requires=['graphviz', 'Jinja2'],
    extras_require={
        'test': ['pytest'],
    },
    include_package_data=True,
    project_urls={
        'Bug Reports': 'https://github.com/dpapathanasiou/simple-graph-pypi/issues',
        'Source': 'https://github.com/dpapathanasiou/simple-graph-pypi/tree/main/src/simple_graph_sqlite',
    },
)
