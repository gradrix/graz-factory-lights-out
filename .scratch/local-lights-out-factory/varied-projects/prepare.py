"""Author frozen specs and independent gates; reference code never enters model input."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMON = '''Create a complete offline Python >=3.11 project using only the standard library
at runtime. Initial source contains only BRIEF.md and archive/preserved.txt.
Produce exactly core.py, cli.py, pyproject.toml, README.md, tests/test_core.py.
Do not change initial files. No network, services or credentials.
'''
CLI = '''Expose main(argv=None)->int in cli.py and support python -m cli. Read UTF-8
input from the one required positional file path. Call core.run(text), print its
JSON result followed by one newline. Success returns 0. Invalid arguments, invalid
input, missing/unreadable files return 2, explanatory stderr, empty stdout, no
traceback. --help returns 0. main must return status for library callers including
argument errors/help. Separate invocations must work. Input files remain unchanged.
'''
PACKAGE = '''Use setuptools.build_meta with build requirements setuptools and wheel.
Distribution NAME-local version 0.1.0, Python >=3.11, no runtime dependencies.
Include top-level modules core and cli. Console script NAME points to cli:main.
Offline pip install --no-deps --no-build-isolation --target DIR . must work.
Invoke installed console entry as python DIR/bin/NAME with DIR on PYTHONPATH from
outside source (sandbox writable directories are noexec). Packaging checks need
core.py and cli.py; declare those task dependencies.
'''
TESTS = '''Create at least six substantive pytest tests in tests/test_core.py using the
real core.run. Cover valid, empty, invalid inputs, ordering and duplicate handling.
Tests must fail implementations that always return [], reverse the result ordering,
or accept invalid input as []. No skips or fake implementation imports. Test work
needs core.py as a declared dependency. README.md must explain installation, CLI
usage, Python API, pytest, input format, ordering and invalid-input behavior.
'''
CORE = {
'csvfold': '''Expose run(text: str)->list[dict] in core.py. Parse CSV with exact header
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
''',
'dagorder': '''Expose run(text: str)->list[str] in core.py. Parse JSON object mapping node
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
'''
}
REF = {
'csvfold': '''import csv, io, re

def run(text):
    if not isinstance(text, str):
        raise ValueError('text required')
    try:
        rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    except csv.Error as exc:
        raise ValueError('invalid CSV') from exc
    if not rows or rows[0] != ['label', 'quantity']:
        raise ValueError('header')
    totals = {}
    for row in rows[1:]:
        if len(row) != 2:
            raise ValueError('fields')
        label, amount = row
        if '\\r' in label or '\\n' in label or not 1 <= len(label.strip()) <= 40:
            raise ValueError('label')
        if not re.fullmatch(r'[+-]?[0-9]+', amount):
            raise ValueError('quantity')
        label = label.strip()
        totals[label] = totals.get(label, 0) + int(amount)
    return [{'label': k, 'quantity': totals[k]} for k in sorted(totals)]
''',
'dagorder': '''import json, re

def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result

def run(text):
    if not isinstance(text, str):
        raise ValueError('text required')
    graph = json.loads(text, object_pairs_hook=_object)
    if not isinstance(graph, dict):
        raise ValueError('object required')
    for node, deps in graph.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', node) or not isinstance(deps, list):
            raise ValueError('node')
        if any(not isinstance(d, str) or d not in graph for d in deps):
            raise ValueError('prerequisite')
        if len(set(deps)) != len(deps):
            raise ValueError('duplicate prerequisite')
    result = []
    remaining = set(graph)
    while remaining:
        ready = sorted(n for n in remaining if all(d in result for d in graph[n]))
        if not ready:
            raise ValueError('cycle')
        result.append(ready[0])
        remaining.remove(ready[0])
    return result
'''
}
VALID = {
'csvfold': [('label,quantity\n', []), ('label,quantity\nz,1\na,2\nz,-1\n', [{'label':'a','quantity':2},{'label':'z','quantity':0}]), ('label,quantity\r\n" café,blue ",+03\r\n', [{'label':'café,blue','quantity':3}])],
'dagorder': [('{}', []), ('{"z":[],"b":["a"],"a":[]}', ['a','b','z']), ('{"c":["a","b"],"b":[],"a":[]}', ['a','b','c'])]
}
INVALID = {
'csvfold': ['', 'label\n', 'quantity,label\n', 'label,quantity,quantity\n', 'label,quantity\n\n', 'label,quantity\na\n', 'label,quantity\na,1,x\n', 'label,quantity\n ,1\n', 'label,quantity\n"\na",1\n', 'label,quantity\na,1.0\n', 'label,quantity\na, 1\n', 'label,quantity\na,١\n', 'label,quantity\n"unterminated,1\n'],
'dagorder': ['', '[]', '{"a":[],"a":[]}', '{"A":[]}', '{"a":{}}', '{"a":[true]}', '{"a":["b"]}', '{"a":["a"]}', '{"a":["b"],"b":["a"]}', '{"a":[],"b":["a","a"]}', '{"a":[],"b":[1]}']
}
CLI_REF = '''import argparse, json, pathlib, sys
import core

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    try:
        result = core.run(pathlib.Path(args.path).read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        print('error:', exc, file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0

if __name__ == '__main__':
    sys.exit(main())
'''


def prepare(name):
    root = HERE / name
    root.mkdir(exist_ok=False)
    reqs = dict(core=CORE[name], cli=CLI, packaging=PACKAGE.replace('NAME', name), tests_docs=TESTS)
    (root/'requirements.json').write_text(json.dumps(reqs, indent=2)+'\n')
    brief = COMMON + '\n' + '\n'.join(reqs.values())
    (root/'brief.md').write_text(brief)
    ref = root/'reference'
    (ref/'tests').mkdir(parents=True)
    (ref/'core.py').write_text(REF[name])
    (ref/'cli.py').write_text(CLI_REF)
    (ref/'pyproject.toml').write_text(f'''[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
[project]
name = "{name}-local"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []
[project.scripts]
{name} = "cli:main"
[tool.setuptools]
py-modules = ["core", "cli"]
''')
    (ref/'README.md').write_text(f'Install {name}: pip install .\nCLI: {name} input.txt\nPython API: core.run(text)\nTest: python -m pytest\nInput format and ordering: '+CORE[name]+'\nInvalid input raises ValueError; CLI returns 2.\n')
    tests = 'import pytest\nimport core\n\n'
    for i,(raw,expected) in enumerate(VALID[name]):
        tests += f'def test_valid_{i}():\n    assert core.run({raw!r}) == {expected!r}\n\n'
    for i,raw in enumerate(INVALID[name]):
        tests += f'def test_invalid_{i}():\n    with pytest.raises(ValueError):\n        core.run({raw!r})\n\n'
    (ref/'tests/test_core.py').write_text(tests)
    checks = root/'checks'; checks.mkdir()
    api = 'import core\nvalid = '+repr(VALID[name])+'\ninvalid = '+repr([None, 1, True, *INVALID[name]])+'''
for raw, expected in valid:
    actual = core.run(raw)
    assert actual == expected, (raw, expected, actual)
for raw in invalid:
    try:
        core.run(raw)
    except ValueError:
        pass
    else:
        raise AssertionError(('invalid accepted', raw))
print('api-ok')
'''
    (checks/'api.py').write_text(api)
    cli = 'VALID = '+repr(VALID[name][1])+'\nINVALID = '+repr(INVALID[name][-1])+'''
import contextlib, io, json, os, pathlib, subprocess, sys, tempfile
import cli

def check(command, code, expected=None, error=False):
    proc = subprocess.run(command, text=True, capture_output=True)
    assert proc.returncode == code, (command, code, proc.returncode, proc.stdout, proc.stderr)
    assert 'Traceback' not in proc.stderr, proc.stderr
    if error:
        assert proc.stderr.strip() and not proc.stdout, (command, proc.stdout, proc.stderr)
    if expected is not None:
        assert json.loads(proc.stdout) == expected, (proc.stdout, expected)
    return proc
with tempfile.TemporaryDirectory() as folder:
    path = pathlib.Path(folder)/'input.txt'
    raw, expected = VALID
    path.write_text(raw, encoding='utf-8')
    check([sys.executable, '-m', 'cli', str(path)], 0, expected)
    assert path.read_text() == raw
    check([sys.executable, '-m', 'cli', '--help'], 0)
    check([sys.executable, '-m', 'cli'], 2, error=True)
    check([sys.executable, '-m', 'cli', str(path)+'missing'], 2, error=True)
    path.write_text(INVALID)
    check([sys.executable, '-m', 'cli', str(path)], 2, error=True)
    assert path.read_text() == INVALID
    for args, status in (([], 2), (['--help'], 0), ([str(path)], 2)):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            actual = cli.main(args)
        assert actual == status, (args, status, actual)
print('cli-ok')
'''
    (checks/'cli.py').write_text(cli)
    (checks/'package.py').write_text('NAME = '+repr(name)+'\nVALID = '+repr(VALID[name][1])+'''
import json, os, pathlib, subprocess, sys, tempfile, tomllib
meta = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
assert meta['build-system']['build-backend'] == 'setuptools.build_meta'
assert set(meta['build-system']['requires']) == {'setuptools', 'wheel'}
assert meta['project']['name'] == NAME+'-local' and meta['project']['version'] == '0.1.0'
assert meta['project']['requires-python'] == '>=3.11'
assert meta['project'].get('dependencies', []) == []
assert meta['project']['scripts'][NAME] == 'cli:main'
assert set(meta['tool']['setuptools']['py-modules']) == {'core', 'cli'}
with tempfile.TemporaryDirectory() as folder:
    target = pathlib.Path(folder)/'installed'
    proc = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-build-isolation', '--target', str(target), '.'], text=True, capture_output=True)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    path = pathlib.Path(folder)/'input.txt'
    path.write_text(VALID[0])
    env = dict(os.environ, PYTHONPATH=str(target))
    proc = subprocess.run([sys.executable, str(target/'bin'/NAME), str(path)], cwd=folder, env=env, text=True, capture_output=True)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert json.loads(proc.stdout) == VALID[1], proc.stdout
    probe = subprocess.run([sys.executable, '-c', 'import core; print(core.__file__)'], cwd=folder, env=env, text=True, capture_output=True)
    assert str(target) in probe.stdout, probe.stdout
print('package-ok')
''')
    (checks/'docs.py').write_text('''from pathlib import Path
text = Path('README.md').read_text().lower()
for word in ('install', 'cli', 'core.run', 'pytest', 'input', 'order', 'invalid'):
    assert word in text, ('missing documentation', word)
assert len(text) >= 250, 'README too small'
print('docs-ok')
''')
    # Mutations replace public behavior, including broad acceptance of invalid input.
    (checks/'tests.py').write_text('''import pathlib, shutil, subprocess, sys, tempfile
source = pathlib.Path('core.py').read_text()
mutants = {
    'empty': '\\ndef run(text):\\n    return []\\n',
    'reverse': '\\n_original = run\\ndef run(text):\\n    return list(reversed(_original(text)))\\n',
    'accept-invalid': '\\n_original = run\\ndef run(text):\\n    try:\\n        return _original(text)\\n    except ValueError:\\n        return []\\n',
}
import ast
tree = ast.parse(pathlib.Path('tests/test_core.py').read_text())
assert len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]) >= 6, 'six tests required'
for name, suffix in [('correct', ''), *mutants.items()]:
    with tempfile.TemporaryDirectory() as folder:
        dest = pathlib.Path(folder)
        (dest/'core.py').write_text(source + suffix)
        shutil.copytree('tests', dest/'tests')
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'], cwd=dest, text=True, capture_output=True)
        assert (result.returncode == 0) if name == 'correct' else (result.returncode == 1), (name, result.returncode, result.stdout, result.stderr)
        assert 'skipped' not in result.stdout and 'xfailed' not in result.stdout, result.stdout
print('tests-ok')
''')

if __name__ == '__main__':
    for name in CORE:
        prepare(name)
