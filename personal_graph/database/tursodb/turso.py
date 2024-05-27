from functools import lru_cache
from pathlib import Path

from typing import Optional, Any, Callable, Tuple

from jinja2 import BaseLoader, Environment, select_autoescape
from personal_graph.database.db import CursorExecFunction
from personal_graph.database.sqlite.sqlite import SQLite

try:
    import libsql_experimental as libsql  # type: ignore
except ImportError:
    pass


@lru_cache(maxsize=None)
def read_sql(sql_file: Path) -> str:
    with open(Path(__file__).parent.resolve() / "raw-queries" / sql_file) as f:
        return f.read()


class SqlTemplateLoader(BaseLoader):
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def get_source(
        self, environment: Environment, template: str
    ) -> Tuple[str, str, Callable[[], bool]]:
        def uptodate() -> bool:
            return True

        template_path = self.templates_dir / template

        # Return the source code, the template name, and the uptodate function
        return read_sql(template_path), template, uptodate


class TursoDB(SQLite):
    def __init__(self, *, url: Optional[str] = None, auth_token: Optional[str] = None):
        self.db_url = url
        self.db_auth_token = auth_token

        self.env = Environment(
            loader=SqlTemplateLoader(Path(__file__).parent / "raw-queries"),
            autoescape=select_autoescape(),
        )
        self.clause_template = self.env.get_template("search-where.template")
        self.search_template = self.env.get_template("search-node.template")
        self.traverse_template = self.env.get_template("traverse.template")

    def __eq__(self, other):
        return self.db_url == other.db_url

    def __repr__(self):
        return (
            f"TursoDB(\n"
            f"    db_url={self.db_url},\n"
            f"    db_auth_token='{self.db_auth_token}'\n"
            f"  ),"
        )

    def atomic(self, cursor_exec_fn: CursorExecFunction) -> Any:
        if not hasattr(self, "_connection"):
            self._connection = libsql.connect(
                database=self.db_url,
                auth_token=self.db_auth_token,
            )

        try:
            cursor = self._connection.cursor()
            cursor.execute("PRAGMA foreign_keys = TRUE;")
            results = cursor_exec_fn(cursor, self._connection)
            self._connection.commit()
        finally:
            pass
        return results

    def save(self):
        self._connection.commit()
