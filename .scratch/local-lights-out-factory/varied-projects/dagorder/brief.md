Create a complete offline Python >=3.11 project using only the standard library
at runtime. Initial source contains only BRIEF.md and archive/preserved.txt.
Produce exactly core.py, cli.py, pyproject.toml, README.md, tests/test_core.py.
Do not change initial files. No network, services or credentials.

Expose run(text: str)->list[str] in core.py. Parse JSON object mapping node
names to prerequisite lists. Names match ASCII [a-z][a-z0-9_]{0,31}. Every
prerequisite must name a key, and lists contain distinct names. Empty object yields
[]. Non-string input, malformed JSON, duplicate JSON object keys, non-object root,
invalid names, non-list values, non-string entries, duplicate prerequisites,
missing prerequisite keys, self-dependencies and cycles raise ValueError.
Return every node exactly once in topological order, prerequisites first. At EACH
step choose the lexicographically smallest currently available node (not whole
sorted layers). Example {"a":[],"b":["a"],"z":[]} -> ["a","b","z"]. Result
must be independent of object-key order and prerequisite-list order. No external
state, graph mutation, network or dynamic code execution.

Expose main(argv=None)->int in cli.py and support python -m cli. Read UTF-8
input from the one required positional file path. Call core.run(text), print its
JSON result followed by one newline. Success returns 0. Invalid arguments, invalid
input, missing/unreadable files return 2, explanatory stderr, empty stdout, no
traceback. --help returns 0. main must return status for library callers including
argument errors/help. Separate invocations must work. Input files remain unchanged.

Use setuptools.build_meta with build requirements setuptools and wheel.
Distribution dagorder-local version 0.1.0, Python >=3.11, no runtime dependencies.
Include top-level modules core and cli. Console script dagorder points to cli:main.
Offline pip install --no-deps --no-build-isolation --target DIR . must work.
Invoke installed console entry as python DIR/bin/dagorder with DIR on PYTHONPATH from
outside source (sandbox writable directories are noexec). Packaging checks need
core.py and cli.py; declare those task dependencies.

Create at least six substantive pytest tests in tests/test_core.py using the
real core.run. Cover valid, empty, invalid inputs, ordering and duplicate handling.
Tests must fail implementations that always return [], reverse the result ordering,
or accept invalid input as []. No skips or fake implementation imports. Test work
needs core.py as a declared dependency. README.md must explain installation, CLI
usage, Python API, pytest, input format, ordering and invalid-input behavior.
