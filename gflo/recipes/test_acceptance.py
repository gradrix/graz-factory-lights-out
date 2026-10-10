"""Mechanical acceptance for a test-writing task; runs in the verification sandbox (standard library only).

python /acceptance/test_acceptance.py  — configuration in /acceptance/test_task.json:
  targets: source files under test; base: {path: sha256} of every tracked file outside tests/ and test/;
  base_tests: {path: sha256} of test files at the base (their contents are in /acceptance/base_tests/);
  runner: argument list with a "{tests}" element; budget_seconds: time allowed for mutant runs;
  threshold: required mutation score of the new tests; max_mutants; runs (repeat count for flakiness).

The candidate passes when every tracked file outside the test directories is unchanged (no new ones either),
no base test file is removed, it adds at least one test function, its new or changed tests contain real
assertions, pass `runs` times in a row and also on a behaviour-preserving reformatting of each target, and
they kill at least `threshold` of the sampled mutants that the base versions of those modules do not kill.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

WORKSPACE = Path("/workspace")
SWAPS = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
         ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In,
         ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult, ast.Div: ast.Mult,
         ast.And: ast.Or, ast.Or: ast.And}


def is_test(path):
    """Only modules under a top-level tests/ or test/ directory are tests; every other file is protected source."""
    return Path(path).parts[0] in ('tests', 'test') and len(Path(path).parts) > 1


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
    """(exit code or 'timeout', elapsed seconds) of the runner on the given test files."""
    command = [piece for part in runner for piece in (tests if part == '{tests}' else [part])]
    started = time.monotonic()
    try:
        code = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1')).returncode
    except subprocess.TimeoutExpired:
        code = 'timeout'
    return code, time.monotonic() - started


def test_functions(source):
    """{qualified test name: source segment} of every test function in a module."""
    tree, found = ast.parse(source), {}
    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, prefix + child.name + '.')
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith('test'):
                found[prefix + child.name] = ast.get_source_segment(source, child) or child.name
    visit(tree, '')
    return found


CACHES = ('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.coverage')
CONFIG_SUFFIXES = ('.py', '.ini', '.cfg', '.toml', '.pth')


def files(root):
    return {path.relative_to(root).as_posix() for path in Path(root).rglob('*')
            if path.is_file() and not any(part in CACHES for part in path.relative_to(root).parts)}


def equivalent(source):
    """Same behaviour, different text, AST and bytecode: a `pass` opens every function body (after its docstring)."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], 'value', None), ast.Constant) \
                and isinstance(node.body[0].value.value, str)
            node.body.insert(1 if docstring else 0, ast.Pass())
    return ast.unparse(ast.fix_missing_locations(tree)) + '\n'


def module_name(target):
    parts = list(Path(target).with_suffix('').parts)
    parts = parts[1:] if parts[0] == 'src' and len(parts) > 1 else parts
    return '.'.join(parts[:-1] if parts[-1] == '__init__' else parts)


def imports_target(source, names):
    """Whether a test module imports a target module or a package containing it (re-exports count)."""
    packages = {name.rsplit('.', depth)[0] for name in names for depth in range(1, name.count('.') + 1)}
    reachable = set(names) | packages
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(alias.name in reachable for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and (
                node.module in reachable or any(f'{node.module}.{alias.name}' in names for alias in node.names)):
            return True
    return False


def main(config_path='/acceptance/test_task.json', workspace=WORKSPACE):
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    base_tests = config_path.parent / 'base_tests'
    workspace = Path(workspace)
    started = time.monotonic()
    problems = []
    for path, expected in config['base'].items():
        current = workspace / path
        if not current.is_file() or digest(current) != expected:
            problems.append(f'non-test file changed or removed: {path}')
    present = files(workspace)
    for relative in sorted(present):
        if relative in config['base'] or relative in config['base_tests']:
            continue
        if not is_test(relative):
            problems.append(f'new file outside the test directories: {relative}')
        elif not Path(relative).name.startswith('test_') and relative.endswith(CONFIG_SUFFIXES):
            problems.append(f'new test-support or configuration file (only test_*.py modules and data may be added): {relative}')
    for path, expected in config['base_tests'].items():
        if path not in present:
            problems.append(f'existing test file removed: {path}')
        elif not Path(path).name.startswith('test_') and digest(workspace / path) != expected:
            problems.append(f'existing test-support file changed: {path}')
    changed = sorted(relative for relative in present if is_test(relative) and Path(relative).name.startswith('test_')
                     and relative.endswith('.py') and config['base_tests'].get(relative) != digest(workspace / relative))
    added = 0
    for path in changed:
        old = test_functions((base_tests / path).read_text()) if (base_tests / path).is_file() else {}
        new = test_functions((workspace / path).read_text())
        fresh = {name for name, text in new.items() if old.get(name) != text}
        added += len(set(new) - set(old))
        problems += [f'{path}: existing test removed: {name}' for name in sorted(set(old) - set(new))]
        problems += [problem for problem in smells(workspace / path) if problem.rsplit('::', 1)[1].split(' ')[0] in
                     {name.rsplit('.', 1)[-1] for name in fresh}]
    if not changed or not added:
        problems.append('no new test function in a test_*.py module under tests/')
    if problems:
        print('\n'.join(problems))
        return 1
    budget = config.get('budget_seconds', 600)
    with tempfile.TemporaryDirectory() as directory:
        copy, base = Path(directory) / 'project', Path(directory) / 'base'
        shutil.copytree(workspace, copy, ignore=shutil.ignore_patterns(*CACHES, '.git'))
        # The base project: candidate files outside the tests (unchanged, checked above) plus the pristine base
        # test tree, so nothing the candidate added under tests/ can influence what the existing tests kill.
        base.mkdir()
        for name in os.listdir(copy):
            if name not in ('tests', 'test'):
                source = copy / name
                (shutil.copytree if source.is_dir() else shutil.copy2)(source, base / name)
        if base_tests.is_dir():
            for name in os.listdir(base_tests):
                shutil.copytree(base_tests / name, base / name, dirs_exist_ok=True)
        elapsed = 0.0
        for attempt in range(config.get('runs', 3)):
            code, seconds = run(config['runner'], changed, copy, max(5.0, budget / 4))
            elapsed = max(elapsed, seconds)
            if code != 0:
                print(f'new tests failed on the unmodified code (run {attempt + 1}: exit {code})')
                return 1
        limit = max(5.0, 5 * elapsed)  # a mutant that loops is killed, a merely slow test is not
        # Tests must check behaviour, not source text: they must pass on an equivalent rewrite of each target.
        for target in config['targets']:
            original = (copy / target).read_text()
            (copy / target).write_text(equivalent(original))
            code, _ = run(config['runner'], changed, copy, limit)
            (copy / target).write_text(original)
            if code != 0:
                print(f'new tests fail on a behaviour-preserving rewrite of {target}: they depend on its source text '
                      'or structure, not its behaviour')
                return 1
        # Existing tests that import a target (as of the base): what they already kill earns nothing.
        names = {module_name(target) for target in config['targets']}
        # Base versions of every changed existing module always count, whatever route they take to the target.
        related = sorted(path for path in config['base_tests'] if Path(path).name.startswith('test_') and path.endswith('.py')
                         and (path in changed or imports_target((base_tests / path).read_text(), names)))
        passing, total = [], 0.0
        for path in related:  # a module that already fails unmodified cannot tell us what is killed
            code, seconds = run(config['runner'], [path], base, max(5.0, budget / 8))
            if code == 0:
                passing.append(path)
                total += seconds
        related = passing
        base_limit = max(5.0, 5 * total)
        deadline = started + budget
        new_kills, eligible, base_kills, survivors = 0, 0, 0, []
        per_target = max(1, config.get('max_mutants', 30) // len(config['targets']))
        for target in config['targets']:
            original = (copy / target).read_text()
            for site, source in mutants(original, per_target):
                if time.monotonic() > deadline:
                    break
                (copy / target).write_text(source)
                (base / target).write_text(source)
                if related and run(config['runner'], related, base, base_limit)[0] != 0:
                    base_kills += 1
                    continue
                eligible += 1
                if run(config['runner'], changed, copy, limit)[0] != 0:
                    new_kills += 1
                else:
                    line = getattr(list(ast.walk(ast.parse(original)))[site[1]], 'lineno', '?')
                    survivors.append(f'{target}:{line} {site[0].replace("_", " ")}')
            (copy / target).write_text(original)
            (base / target).write_text(original)
    score = new_kills / eligible if eligible else 0.0
    print(f'tests: {", ".join(changed)}; {added} new test functions; existing related tests: {len(related)} modules, '
          f'already killing {base_kills} mutants; of the rest the new tests kill {new_kills}/{eligible} = {score:.2f} '
          f'(required {config["threshold"]})')
    if not eligible:
        print('no mutant was left to score: either the existing tests already kill every sampled mutant (choose a less '
              'tested target) or the time budget ran out before mutants could be evaluated')
    for line in survivors[:15]:
        print('SURVIVED', line)
    return 0 if eligible and score >= config['threshold'] else 1


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
