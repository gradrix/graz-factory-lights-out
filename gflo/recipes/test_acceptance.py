"""Mechanical acceptance for a test-writing task; runs in the verification sandbox (standard library only).

python /acceptance/test_acceptance.py  — configuration in /acceptance/test_task.json:
  targets: source files under test; base: {path: sha256} of every non-test Python file at the base commit;
  base_tests: {path: sha256} of test files at the base; runner: argument list with a "{tests}" element;
  threshold: required mutation score of the new tests; max_mutants; runs (repeat count for flakiness).

The candidate passes when non-test Python is unchanged, at least one test file is new or changed, the
changed tests contain real assertions, pass `runs` times in a row, and kill at least `threshold` of the
sampled mutants of the targets.
"""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

WORKSPACE = Path("/workspace")
SWAPS = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
         ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In,
         ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult, ast.Div: ast.Mult,
         ast.And: ast.Or, ast.Or: ast.And}


def is_test(path):
    parts = Path(path).parts
    return 'tests' in parts or 'test' in parts or Path(path).name.startswith('test_') or Path(path).name.endswith('_test.py')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mutation_sites(tree):
    """(kind, node index, detail) for every mutable site, in a stable order."""
    sites = []
    for index, node in enumerate(ast.walk(tree)):
        if isinstance(node, ast.Compare):
            sites += [('compare', index, position) for position, op in enumerate(node.ops) if type(op) in SWAPS]
        elif isinstance(node, (ast.BinOp, ast.BoolOp)) and type(node.op) in SWAPS:
            sites.append(('operator', index, None))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            sites.append(('drop_not', index, None))
        elif isinstance(node, ast.Constant) and type(node.value) in (bool, int):
            sites.append(('constant', index, None))
        elif isinstance(node, ast.Return) and node.value is not None and not (isinstance(node.value, ast.Constant) and node.value.value is None):
            sites.append(('return_none', index, None))
    return sites


def apply(tree, site):
    """Mutate the site (numbered in ast.walk order, as by mutation_sites) in place."""
    kind, target, detail = site
    nodes = list(ast.walk(tree))
    node = nodes[target]
    if kind == 'compare':
        node.ops[detail] = SWAPS[type(node.ops[detail])]()
    elif kind == 'operator':
        node.op = SWAPS[type(node.op)]()
    elif kind == 'drop_not':
        for parent in nodes:
            for field, value in ast.iter_fields(parent):
                if value is node:
                    setattr(parent, field, node.operand)
                elif isinstance(value, list) and any(item is node for item in value):
                    value[[id(item) for item in value].index(id(node))] = node.operand
    elif kind == 'constant':
        node.value = (not node.value) if isinstance(node.value, bool) else node.value + 1
    elif kind == 'return_none':
        node.value = ast.Constant(None)
    return ast.fix_missing_locations(tree)


def mutants(source, limit):
    """Up to `limit` mutated sources, sampled evenly across all sites (deterministic)."""
    sites = mutation_sites(ast.parse(source))
    if len(sites) > limit:
        step = len(sites) / limit
        sites = [sites[int(i * step)] for i in range(limit)]
    for site in sites:
        mutated = ast.unparse(apply(ast.parse(source), site))
        if mutated != ast.unparse(ast.parse(source)):
            yield site, mutated


def smells(path):
    """Test functions without a real assertion, or with only trivially true ones."""
    found = []
    tree = ast.parse(Path(path).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test'):
            body = list(ast.walk(node))
            asserts = [n for n in body if isinstance(n, ast.Assert)]
            calls = [n for n in body if isinstance(n, ast.Call) and (
                (isinstance(n.func, ast.Attribute) and (n.func.attr.startswith('assert') or n.func.attr in ('raises', 'fail')))
                or (isinstance(n.func, ast.Name) and n.func.id.startswith('assert')))]
            withs = [n for n in body if isinstance(n, ast.With) and any(
                isinstance(item.context_expr, ast.Call) and isinstance(item.context_expr.func, ast.Attribute)
                and item.context_expr.func.attr in ('raises', 'assertRaises', 'assertRaisesRegex') for item in n.items)]
            trivial = [a for a in asserts if isinstance(a.test, ast.Constant) and a.test.value]
            if not (asserts or calls or withs) or (asserts and len(trivial) == len(asserts) and not calls and not withs):
                found.append(f'{path}::{node.name} has no meaningful assertion')
    return found


def run(runner, tests, cwd, timeout):
    command = [piece for part in runner for piece in (tests if part == '{tests}' else [part])]
    try:
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        return 'timeout'


def main(config_path='/acceptance/test_task.json', workspace=WORKSPACE):
    config = json.loads(Path(config_path).read_text())
    workspace = Path(workspace)
    problems = []
    for path, expected in config['base'].items():
        current = workspace / path
        if not current.is_file() or digest(current) != expected:
            problems.append(f'non-test source changed or removed: {path}')
    for path in workspace.rglob('*.py'):
        relative = path.relative_to(workspace).as_posix()
        if not is_test(relative) and relative not in config['base']:
            problems.append(f'new non-test Python file: {relative}')
    changed = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob('*.py')
                     if is_test(path.relative_to(workspace).as_posix()) and path.name.startswith('test')
                     and config['base_tests'].get(path.relative_to(workspace).as_posix()) != digest(path))
    if not changed:
        problems.append('no new or changed test module (test_*.py)')
    for path in changed:
        problems += smells(workspace / path)
    if problems:
        print('\n'.join(problems))
        return 1
    with tempfile.TemporaryDirectory() as directory:
        copy = Path(directory) / 'project'
        shutil.copytree(workspace, copy, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        for attempt in range(config.get('runs', 3)):
            code = run(config['runner'], changed, copy, 300)
            if code != 0:
                print(f'new tests failed on the unmodified code (run {attempt + 1}: exit {code})')
                return 1
        killed, total, survivors = 0, 0, []
        for target in config['targets']:
            original = (copy / target).read_text()
            for site, source in mutants(original, config.get('max_mutants', 30) // max(1, len(config['targets']))):
                total += 1
                (copy / target).write_text(source)
                code = run(config['runner'], changed, copy, 60)
                if code != 0:
                    killed += 1
                else:
                    line = getattr(list(ast.walk(ast.parse(original)))[site[1]], 'lineno', '?')
                    survivors.append(f'{target}:{line} {site[0].replace("_", " ")}')
            (copy / target).write_text(original)
    score = killed / total if total else 0.0
    print(f'tests: {", ".join(changed)}; mutants killed {killed}/{total} = {score:.2f} (required {config["threshold"]})')
    for line in survivors[:15]:
        print('SURVIVED', line)
    return 0 if total and score >= config['threshold'] else 1


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
