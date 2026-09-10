import os
import subprocess
import sys

import pytest

from gflo.test_adequacy import FaultyVariant, pytest_adequacy_gate


def execute(tmp_path, test, faulty='def value(): return 0\n'):
    (tmp_path / 'subject.py').write_text('def value(): return 7\n')
    (tmp_path / 'test_subject.py').write_text(test)
    gate = pytest_adequacy_gate(('test_subject.py',), (
        FaultyVariant(name='wrong-value', modules={'subject': faulty}),
    ))
    case = gate.cases[0]
    return subprocess.run(
        [sys.executable, *case.command[1:]], input=case.stdin, text=True,
        capture_output=True, cwd=tmp_path, timeout=30,
        env={**os.environ, 'PYTHONPATH': str(tmp_path)},
    )


def test_rejects_faulty_behavior(tmp_path):
    result = execute(tmp_path, 'from subject import value\ndef test_value(): assert value() == 7\n')
    assert result.returncode == 0, result.stderr
    assert result.stdout == 'test-adequacy-ok\n'


@pytest.mark.parametrize('test, faulty, diagnostic', [
    ('def test_noop(): assert True\n', 'def value(): return 0\n', 'did not reject'),
    ('from subject import value\ndef test_value(): assert value() == 7\n',
     'def value(): raise RuntimeError("broken")\n', 'errors/skips'),
    ('from subject import value\ndef test_value(): assert value() == 7\n',
     'raise ImportError("broken")\n', 'process failed'),
    ('import pytest\n@pytest.mark.skip\ndef test_skip(): pass\n',
     'def value(): return 0\n', 'errors/skips'),
    ('import pytest\n@pytest.mark.xfail\ndef test_xfail(): assert False\n',
     'def value(): return 0\n', 'errors/skips'),
    ('from subject import value\ndef test_value(): assert value() == 9\n',
     'def value(): return 0\n', 'AssertionError'),
    ('from subject import missing\ndef test_value(): assert missing\n',
     'def value(): return 0\n', 'AssertionError'),
])
def test_does_not_confuse_errors_or_vacuous_tests_with_detection(tmp_path, test, faulty, diagnostic):
    result = execute(tmp_path, test, faulty)
    assert result.returncode != 0
    assert diagnostic in result.stderr


def test_gate_identity_binds_faulty_source():
    one = pytest_adequacy_gate(('test_a.py',), (FaultyVariant(name='fault', modules={'a': 'x=1'}),))
    two = pytest_adequacy_gate(('test_a.py',), (FaultyVariant(name='fault', modules={'a': 'x=2'}),))
    assert one.digest() != two.digest()


@pytest.mark.parametrize('path', ['/test_a.py', '../test_a.py', '-test_a.py', 'a//test_a.py'])
def test_rejects_unsafe_test_paths(path):
    with pytest.raises(ValueError):
        pytest_adequacy_gate((path,), (FaultyVariant(name='fault', modules={'a': 'x=1'}),))


def test_collection_skip_cannot_hide_beside_passing_test(tmp_path):
    (tmp_path / 'subject.py').write_text('def value(): return 7\n')
    (tmp_path / 'test_good.py').write_text(
        'from subject import value\ndef test_value(): assert value() == 7\n')
    (tmp_path / 'test_hidden.py').write_text(
        'import pytest\npytest.skip("hidden", allow_module_level=True)\n')
    gate = pytest_adequacy_gate(('test_good.py', 'test_hidden.py'), (
        FaultyVariant(name='fault', modules={'subject': 'def value(): return 0\n'}),))
    case = gate.cases[0]
    result = subprocess.run([sys.executable, *case.command[1:]], input=case.stdin,
        text=True, capture_output=True, cwd=tmp_path, timeout=30,
        env={**os.environ, 'PYTHONPATH': str(tmp_path)})
    assert result.returncode != 0
    assert 'errors/skips' in result.stderr


def test_assertion_on_one_input_does_not_hide_crash_on_another(tmp_path):
    tests = (
        'from subject import value\n'
        'def test_first(): assert value(1) == 7\n'
        'def test_second(): assert value(0) == 7\n'
    )
    (tmp_path / 'subject.py').write_text('def value(x): return 7\n')
    (tmp_path / 'test_subject.py').write_text(tests)
    variant = FaultyVariant(name='mixed-failure', modules={
        'subject': 'def value(x):\n    return 0 if x else 1 / 0\n',
    })
    case = pytest_adequacy_gate(('test_subject.py',), (variant,)).cases[0]
    result = subprocess.run([sys.executable, *case.command[1:]], input=case.stdin,
        text=True, capture_output=True, cwd=tmp_path, timeout=30,
        env={**os.environ, 'PYTHONPATH': str(tmp_path)})
    assert result.returncode != 0
    assert 'errors/skips' in result.stderr
    assert 'ZeroDivisionError' in result.stderr
