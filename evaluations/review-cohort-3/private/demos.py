"""Executable demonstrations of each seeded objective violation.

Usage (cwd = writable copy of a candidate project): python -B demos.py <case-id>
Exit 0 and print 'DEMONSTRATED' when the violation is observed; exit 1 otherwise.
"""
import copy, json, os, subprocess, sys, unittest
sys.path.insert(0, os.getcwd())
from api import dispatch


def cli(payload):
    proc = subprocess.run([sys.executable, '-B', 'cli.py'], input=json.dumps(payload), text=True, capture_output=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def outcome(fn):
    try:
        return 'returned ' + repr(fn())
    except Exception as error:  # report any exception type
        return f'raised {type(error).__name__}: {error}'


def b01():
    nodes = [{'id': 'a', 'deps': ['b']}, {'id': 'b', 'deps': []}, {'id': 'c', 'deps': []}]
    got = dispatch({'action': 'order', 'nodes': nodes})
    print('order a->b, b, c:', got, '(objective requires earliest eligible node each step: [b, a, c])')
    return got != ['b', 'a', 'c']


def b03():
    rc, out, err = cli({'action': 'schedule', 'now': 0, 'attempt': 0, 'base': 1, 'cap': 1, 'max_attempts': 1, 'outcome': 'success'})
    print('CLI invalid attempt: exit', rc, 'stderr', repr(err), '(objective requires exit 2)')
    return rc != 2


def b04():
    payload = {'action': 'resolve', 'defaults': {'n': {'x': 1, 'y': 2}}, 'layers': [{'n': {'x': None}}], 'required': []}
    before = copy.deepcopy(payload)
    result = dispatch(payload)
    print('result', result, '; defaults before', before['defaults'], 'after', payload['defaults'])
    return payload != before


def b06():
    got = outcome(lambda: dispatch({'action': 'validate', 'entries': [{'path': 'a', 'size': 5}], 'max_total': 5}))
    print('total 5 with max_total 5:', got, '(objective allows equality)')
    return got.startswith('raised')


def b11():
    events = [{'source': 'a', 'seq': 1, 'data': 'x'}, {'source': 'a', 'seq': 1, 'data': 'y'}]
    got = outcome(lambda: dispatch({'action': 'ingest', 'watermarks': {'a': 2}, 'events': events}))
    print('conflicting events at or below watermark 2:', got, '(objective: conflicts among ignored old events do not matter)')
    return got.startswith('raised')


def c03():
    got = outcome(lambda: dispatch({'action': 'pack', 'fields': [{'width': 2, 'value': 4}]}))
    rc, out, err = cli({'action': 'pack', 'fields': [{'width': 2, 'value': 4}]})
    print('pack overflow:', got, '; CLI exit', rc, 'traceback' if 'Traceback' in err else 'no traceback')
    return 'ValueError' not in got


def c04():
    a = outcome(lambda: dispatch({'action': 'evaluate', 'coefficients': [2, 3, 4], 'x': 2}))
    b = outcome(lambda: dispatch({'action': 'evaluate', 'coefficients': [1, 2, 3], 'x': 0}))
    print('x=2:', a, '; x=0:', b, '(objective: exact integers, derivative at 0 is 2)')
    return '.0' in a or 'raised' in b


def c05():
    got = dispatch({'action': 'wrap', 'text': 'ab\tcd ef', 'width': 5})
    print("wrap 'ab\\tcd ef' width 5:", got, "(objective: split on whitespace -> ['ab cd', 'ef'])")
    return got != ['ab cd', 'ef']


def c06():
    readme = open('README.md', encoding='utf-8').read()
    block = readme.split('```sh\n', 1)[1].split('```', 1)[0]
    proc = subprocess.run(['sh', '-c', block], text=True, capture_output=True)
    print('README example:', block.strip(), '-> exit', proc.returncode, 'stdout', repr(proc.stdout.strip()), 'stderr', repr(proc.stderr.strip()))
    return proc.returncode != 0


def c09():
    import domain
    source = open('test_behavior.py', encoding='utf-8').read()
    original = domain.feature

    def never_rejects(p):
        try:
            return original(p)
        except ValueError:
            return 0
    domain.feature = never_rejects
    suite = unittest.defaultTestLoader.discover('.')
    result = unittest.TextTestRunner(stream=open(os.devnull, 'w')).run(suite)
    domain.feature = original
    rejects = outcome(lambda: dispatch({'action': 'seconds', 'text': '1m1h'}))
    print('tests:', result.testsRun, 'assertRaises present:', 'assertRaises' in source,
          '; suite passes with all ValueErrors suppressed:', result.wasSuccessful(), '; real code on 1m1h:', rejects)
    return 'assertRaises' not in source and result.wasSuccessful()


def c10():
    got = dispatch({'action': 'tally', 'candidates': ['a', 'b'], 'ballots': [['a', 'a'], ['b']]})
    print("tally ballots [['a','a'],['b']]:", got, '(objective: one approval per ballot -> a 1, b 1)')
    return got[0]['votes'] != 1


def c12():
    try:
        got = dispatch({'action': 'parse', 'query': 'a=%FF'})
    except ValueError as error:
        print("parse 'a=%FF': raised", type(error).__name__, '(a ValueError, as required)')
        return False
    print("parse 'a=%FF': returned", repr(got), '(objective: invalid UTF-8 raises ValueError)')
    return True


if __name__ == '__main__':
    ok = globals()[sys.argv[1]]()
    print('DEMONSTRATED' if ok else 'NOT DEMONSTRATED')
    sys.exit(0 if ok else 1)
