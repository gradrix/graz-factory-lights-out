"""Compile trusted faulty-module examples into a portable pytest ProcessGate."""

from __future__ import annotations

import json
import re
from typing import Annotated

from pydantic import Field

from gflo.gates import ProcessCase, ProcessGate
from gflo.records import Record


class FaultyVariant(Record):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    modules: Annotated[dict[str, str], Field(min_length=1, max_length=8)]


# Embedded deliberately: the pinned worker image needs pytest, not an installed GFLO.
_PYTEST_RUNNER = r"""
import contextlib, importlib, io, json, sys, types
payload = json.loads(sys.stdin.read())
for name, source in payload['modules'].items():
    parent, _, child = name.rpartition('.')
    package = importlib.import_module(parent) if parent else None
    module = types.ModuleType(name)
    module.__file__ = name.replace('.', '/') + '.py'
    module.__package__ = parent
    sys.modules[name] = module
    if package is not None:
        setattr(package, child, module)
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
import pytest
class Counts:
    def __init__(self):
        self.ids = []; self.assertions = 0; self.errors = 0; self.skipped = 0
    def pytest_collection_finish(self, session):
        self.ids = sorted(item.nodeid for item in session.items)
    def pytest_runtest_makereport(self, item, call):
        if call.excinfo is not None:
            if call.when == 'call' and call.excinfo.errisinstance(AssertionError):
                self.assertions += 1
            else:
                self.errors += 1
    def pytest_collectreport(self, report):
        if report.skipped:
            self.skipped += 1
        if report.failed:
            self.errors += 1
    def pytest_runtest_logreport(self, report):
        if report.skipped or hasattr(report, 'wasxfail'):
            self.skipped += 1
counts = Counts()
output = io.StringIO()
with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
    result = pytest.main(['-q', '--tb=short', '-o', 'addopts=', *payload['tests']],
                         plugins=[counts])
print(json.dumps(dict(exit=int(result), ids=counts.ids, assertions=counts.assertions,
                      errors=counts.errors, skipped=counts.skipped,
                      detail=output.getvalue()[-6000:])))
"""

_HARNESS = r"""
import json, os, subprocess, sys
spec = json.loads(sys.stdin.read())
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
def run(name, modules):
    result = subprocess.run([sys.executable, '-c', spec['runner']],
        input=json.dumps(dict(modules=modules, tests=spec['tests'])),
        text=True, capture_output=True, env=env, timeout=spec['seconds'])
    if result.returncode:
        raise AssertionError(name + ': validation process failed: ' + result.stderr[-2000:])
    try:
        report = json.loads(result.stdout)
    except ValueError:
        raise AssertionError(name + ': malformed validation report') from None
    if report['errors'] or report['skipped']:
        raise AssertionError(name + ': errors/skips are not behavioral evidence: '
                             + report['detail'])
    return report
base = run('candidate', {})
assert base['exit'] == 0 and len(base['ids']) >= spec['minimum_tests'], base['detail']
for variant in spec['variants']:
    report = run(variant['name'], variant['modules'])
    assert report['ids'] == base['ids'], variant['name'] + ': collected tests changed'
    assert report['exit'] == 1 and report['assertions'] > 0, (
        variant['name'] + ': tests did not reject faulty behavior: ' + report['detail'])
print('test-adequacy-ok')
"""


def pytest_adequacy_gate(
    tests: tuple[str, ...],
    variants: tuple[FaultyVariant, ...],
    *,
    minimum_tests: int = 1,
    seconds: float = 30,
) -> ProcessGate:
    """Caller supplies trusted variants; never promote worker proposals to gates.

    Each variant replaces complete Python modules before test collection. All runs
    use fresh interpreters in the existing offline broker. This detects specified
    faulty behavior, not general correctness or adversarial test manipulation.
    """
    if not tests or len(tests) > 16 or not 1 <= minimum_tests <= 10000:
        raise ValueError("Require bounded test paths and a positive test count")
    if not variants or len(variants) > 8 or len({v.name for v in variants}) != len(variants):
        raise ValueError("Require one to eight uniquely named faulty variants")
    for path in tests:
        if (
            not re.fullmatch(r"[A-Za-z0-9_./-]+\.py", path)
            or any(p in ("", ".", "..") for p in path.split("/"))
            or path.startswith("-")
        ):
            raise ValueError("Tests must be relative Python file paths")
    for variant in variants:
        if any(not re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", m) for m in variant.modules):
            raise ValueError("Variants must name Python modules")
    payload = json.dumps(
        dict(
            runner=_PYTEST_RUNNER,
            tests=tests,
            variants=[v.model_dump(mode="json") for v in variants],
            minimum_tests=minimum_tests,
            seconds=seconds,
        ),
        sort_keys=True,
    )
    return ProcessGate(
        cases=(
            ProcessCase(
                command=("python", "-c", _HARNESS),
                stdin=payload,
                expected_stdout="test-adequacy-ok\n",
                seconds=seconds,
            ),
        )
    )
