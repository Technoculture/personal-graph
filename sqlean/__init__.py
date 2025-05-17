import sqlite3

class Connection:
    def __init__(self, conn):
        self._conn = conn
    def __getattr__(self, name):
        return getattr(self._conn, name)
    def enable_load_extension(self, flag):
        pass

class Cursor:
    def __init__(self, cur):
        self._cur = cur
    def __getattr__(self, name):
        return getattr(self._cur, name)

def connect(*args, **kwargs):
    return Connection(sqlite3.connect(*args, **kwargs))
