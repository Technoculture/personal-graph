from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
sql = (here / "sql")

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='simple-graph-sqlite',
    version='2.0.1',
    description='A simple graph database in SQLite',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dpapathanasiou/simple-graph',
    author='Denis Papathanasiou',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.6, <4',
    install_requires=['graphviz'],
    extras_require={
        'test': ['pytest'],
    },
    package_data={
        'sql': [f'sql/{file.name}' for file in sql.glob('*.sql')],
    },
    project_urls={
        'Bug Reports': 'https://github.com/dpapathanasiou/simple-graph/issues',
        'Source': 'https://github.com/dpapathanasiou/simple-graph/tree/main/python',
    },
)
