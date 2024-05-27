from jinja2 import BaseLoader, Environment, Template
import libsql_experimental as libsql  # type: ignore

from pathlib import Path
from personal_graph.persistence_layer.database.sqlite.sqlite import SQLite as SQLite
from typing import Any, Callable, Tuple, Optional

CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]

def read_sql(sql_file: Path) -> str: ...

class SqlTemplateLoader(BaseLoader):
    templates_dir: Path
    def __init__(self, templates_dir: Path) -> None: ...
    def get_source(
        self, environment: Environment, template: str
    ) -> Tuple[str, str, Callable[[], bool]]: ...

class TursoDB(SQLite):
    db_url: Optional[str]
    db_auth_token: Optional[str]
    env: Environment
    clause_template: Template
    search_template: Template
    traverse_template: Template
    def __init__(
        self, *, url: str | None = None, auth_token: str | None = None
    ) -> None: ...
    def __eq__(self, other): ...
    def atomic(self, cursor_exec_fn: CursorExecFunction) -> Any: ...
    def save(self) -> None: ...
