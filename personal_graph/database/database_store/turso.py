import libsql_experimental as libsql  # type: ignore
from typing import Optional, Any, Callable

from personal_graph.database.database_store.sqlite import SQLite

CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


class TursoDB(SQLite):
    def __init__(self, *, url: Optional[str] = None, auth_token: Optional[str] = None):
        super().__init__()
        self.db_url = url
        self.db_auth_token = auth_token

    def __eq__(self, other):
        return self.db_url == other.db_url

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
