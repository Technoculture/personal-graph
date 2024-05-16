from abc import ABC, abstractmethod

import sqlean as sqlite3  # type: ignore
import libsql_experimental as libsql  # type: ignore
from typing import Any, Callable, Optional

CursorExecFunction = Callable[[libsql.Cursor, libsql.Connection], Any]


class PersistenceLayer(ABC):
    @abstractmethod
    def atomic(self, cursor_exec_fn: CursorExecFunction) -> Any:
        pass

    @abstractmethod
    def save(self):
        pass


# TursoDB persistence layer
class TursoDB(PersistenceLayer):
    def __init__(self, *, url: Optional[str] = None, auth_token: Optional[str] = None):
        self.db_url = url
        self.db_auth_token = auth_token

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


# SQlite persistence layer
class SQLite(PersistenceLayer):
    def __init__(
        self,
        *,
        use_in_memory: bool = False,
        local_path: Optional[str] = None,
        vector0_so_path: Optional[str] = None,
        vss0_so_path: Optional[str] = None,
    ):
        self.use_in_memory = use_in_memory
        self.vector0_so_path = vector0_so_path
        self.vss0_so_path = vss0_so_path
        self.local_path = local_path

    def atomic(self, cursor_exec_fn: CursorExecFunction) -> Any:
        if not hasattr(self, "_connection"):
            if self.use_in_memory:
                self._connection = sqlite3.connect(":memory:")
            else:
                self._connection = sqlite3.connect(self.local_path)

            self._connection.enable_load_extension(True)
            if self.vector0_so_path and self.vss0_so_path:
                self._connection.load_extension(self.vector0_so_path)
                self._connection.load_extension(self.vss0_so_path)
            else:
                raise ValueError(
                    "vector0_so_path and vss0_so_path must be provided when use_in_memory is True."
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
