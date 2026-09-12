Create a complete offline Python >=3.11 project using only the standard library
at runtime. Initial source contains only BRIEF.md and archive/preserved.txt.
Produce exactly core.py, cli.py, pyproject.toml, README.md, tests/test_core.py.
Do not change initial files. No network, services or credentials.

Expose run(text: str)->list[dict] in core.py. Parse CSV with exact header
label,quantity in that order. CSV quoting and embedded commas are supported.
Empty text, missing/wrong/extra/duplicate header fields, extra/missing row fields,
blank data rows, malformed quotes, and non-string input raise ValueError. A header
alone produces []. Each label must be a string whose stripped form is 1..40
characters; reject CR or LF anywhere in the raw label. Trim labels, preserve case
and Unicode. Quantities match ASCII [+-]?[0-9]+ exactly with no whitespace; no
float or exponent notation. Sum integer quantities per normalized label, including
negative and zero totals, with no input-order dependence. Return one dict per label
exactly {"label": label, "quantity": integer_total}, sorted by label using Python
string ordering. Support LF and CRLF row endings. Do not mutate external state.

Expose main(argv=None)->int in cli.py and support python -m cli. Read UTF-8
input from the one required positional file path. Call core.run(text), print its
JSON result followed by one newline. Success returns 0. Invalid arguments, invalid
input, missing/unreadable files return 2, explanatory stderr, empty stdout, no
traceback. --help returns 0. main must return status for library callers including
argument errors/help. Separate invocations must work. Input files remain unchanged.

Use setuptools.build_meta with build requirements setuptools and wheel.
Distribution csvfold-local version 0.1.0, Python >=3.11, no runtime dependencies.
Include top-level modules core and cli. Console script csvfold points to cli:main.
Offline pip install --no-deps --no-build-isolation --target DIR . must work.
Invoke installed console entry as python DIR/bin/csvfold with DIR on PYTHONPATH from
outside source (sandbox writable directories are noexec). Packaging checks need
core.py and cli.py; declare those task dependencies.

Create at least six substantive pytest tests in tests/test_core.py using the
real core.run. Cover valid, empty, invalid inputs, ordering and duplicate handling.
Tests must fail implementations that always return [], reverse the result ordering,
or accept invalid input as []. No skips or fake implementation imports. Test work
needs core.py as a declared dependency. README.md must explain installation, CLI
usage, Python API, pytest, input format, ordering and invalid-input behavior.
