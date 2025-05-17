import inspect
import types
import pytest

# Import conftest to register fixtures
import tests.conftest  # noqa: F401

FIXTURES = pytest._fixtures


def _resolve_fixture(name, cache):
    if name in cache:
        return cache[name]
    func = FIXTURES[name]
    sig = inspect.signature(func)
    kwargs = {p: _resolve_fixture(p, cache) for p in sig.parameters}
    res = func(**kwargs)
    if isinstance(res, types.GeneratorType):
        val = next(res)
        cache[name] = val
        def finalizer():
            try:
                next(res)
            except StopIteration:
                pass
        cache.setdefault('_finalizers', []).append(finalizer)
        return val
    else:
        cache[name] = res
        return res


def run_test(func):
    cache = {}
    args = []
    for name in inspect.signature(func).parameters:
        args.append(_resolve_fixture(name, cache))
    func(*args)
    for fin in reversed(cache.get('_finalizers', [])):
        fin()


def main():
    modules = ['tests.test_graph', 'tests.test_visualizers']
    failures = 0
    total = 0
    for mod_name in modules:
        mod = __import__(mod_name, fromlist=['dummy'])
        for name, func in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith('test_'):
                total += 1
                try:
                    run_test(func)
                except AssertionError as e:
                    print(f"FAIL: {mod_name}.{name}: {e}")
                    failures += 1
                except Exception as e:
                    print(f"ERROR: {mod_name}.{name}: {e}")
                    failures += 1
    if failures:
        print(f"{failures}/{total} tests failed")
        raise SystemExit(1)
    print(f"{total} tests passed")


if __name__ == '__main__':
    main()
