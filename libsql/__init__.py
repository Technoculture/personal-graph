class Cursor:
    def execute(self, *args, **kwargs):
        pass

class Connection:
    def cursor(self):
        return Cursor()
    def commit(self):
        pass

def connect(*args, **kwargs):
    return Connection()
