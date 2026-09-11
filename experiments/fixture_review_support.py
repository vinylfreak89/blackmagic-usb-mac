"""Source-preserving mutation support for synthetic fixture reviews.

The verifier now inspects and mutates selftest too. Its caller's mutant must
therefore retain the function name and supply its ACTUAL source to linecache;
an opaque exec function causes an introspection error, not a deciding test.
No files, captures or subprocesses are opened here.
"""
import contextlib
import linecache

import switch_fixtures as fixtures


@contextlib.contextmanager
def compiled_selftest(source):
    original = fixtures.selftest
    filename = "<fixture-review-selftest-%d>" % id(source)
    previous_cache = linecache.cache.get(filename)
    linecache.cache[filename] = (len(source), None, source.splitlines(keepends=True), filename)
    try:
        exec(compile(source, filename, "exec"), fixtures.__dict__)
        yield fixtures.selftest
    finally:
        fixtures.selftest = original
        if previous_cache is None:
            linecache.cache.pop(filename, None)
        else:
            linecache.cache[filename] = previous_cache
