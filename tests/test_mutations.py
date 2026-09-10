import ast

import pytest

from gflo.mutations import propose_faults


def test_deterministic_bounded_independent_mutations():
    source = 'def f(x):\n    if x > 0:\n        return x.strip()\n    return x\n'
    variants = propose_faults('subject', source, 'f')
    assert variants == propose_faults('subject', source, 'f')
    assert len(variants) == 3
    assert len(propose_faults('subject', source, 'f', limit=1)) == 1
    contents = [v.modules['subject'] for v in variants]
    assert sum('not x > 0' in c for c in contents) == 1
    assert sum('x <= 0' in c for c in contents) == 1
    assert sum('strip' not in c for c in contents) == 1
    for content in contents:
        compile(content, '<test>', 'exec')


def test_selection_preserves_other_functions():
    source = 'def outside(x):\n    return x.strip()\nclass C:\n    def f(self,x):\n        return x.strip()\n'
    variant, = propose_faults('subject', source, 'C.f')
    assert ast.dump(ast.parse(source).body[0]) == ast.dump(ast.parse(variant.modules['subject']).body[0])


@pytest.mark.parametrize('name', ['missing', 'C', 'C.missing', ''])
def test_bad_selection(name):
    with pytest.raises(ValueError):
        propose_faults('subject', 'class C:\n    pass\n', name)


def test_no_source_execution():
    assert propose_faults('subject', 'raise RuntimeError()\ndef f(): return 1\n', 'f') == ()
