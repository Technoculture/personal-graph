class raises:
    def __init__(self, exc):
        self.exc = exc
        self.caught = None
        self.value = None
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError(f"{self.exc} not raised")
        if not issubclass(exc_type, self.exc):
            return False
        self.caught = exc
        self.value = exc
        return True

_fixtures = {}

def fixture(func):
    _fixtures[func.__name__] = func
    return func
