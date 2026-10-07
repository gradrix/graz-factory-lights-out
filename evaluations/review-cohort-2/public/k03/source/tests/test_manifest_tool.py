"""Regression tests for the manifest tool (run with:
python -m unittest discover -s . from the project root)."""
import json
import subprocess
import sys
from pathlib import Path
import unittest

from manifest_tool import api, domain, report, validation

SHA_A = 'a' * 64
SHA_B = 'b' * 64
SHA_C = 'c' * 64


def entry(path, size, sha):
    return {'path': path, 'size': size, 'sha256': sha}


class CompareBasics(unittest.TestCase):
    def test_added_removed_modified_unchanged(self):
        """Ordinary behavior: each kind of change lands in the right bucket."""
        before = [entry('a/keep', 3, SHA_A), entry('d/chg', 1, SHA_B),
                  entry('z/gone', 9, SHA_C)]
        after = [entry('a/keep', 3, SHA_A), entry('d/chg', 2, SHA_B),
                 entry('n/new', 4, SHA_C)]
        result = domain.compare(before, after)
        self.assertEqual(result, {
            'added': ['n/new'],
            'removed': ['z/gone'],
            'modified': [{'path': 'd/chg', 'before_size': 1, 'after_size': 2}],
            'renamed': [],
            'unchanged': ['a/keep'],
        })
        # Same size but different hash counts as modified.
        same_size = domain.compare([entry('x', 5, SHA_A)], [entry('x', 5, SHA_B)])
        self.assertEqual(same_size['modified'],
                         [{'path': 'x', 'before_size': 5, 'after_size': 5}])
        self.assertEqual(same_size['unchanged'], [])

    def test_empty_manifests(self):
        """Edge case: empty inputs produce five empty lists."""
        result = domain.compare([], [])
        self.assertEqual(result, {'added': [], 'removed': [],
                                  'modified': [], 'renamed': [],
                                  'unchanged': []})

    def test_unique_signature_rename(self):
        """A rename is recognized only for a 1-to-1 signature match."""
        before = [entry('old/name', 10, SHA_A), entry('keep', 1, SHA_B)]
        after = [entry('new/name', 10, SHA_A), entry('keep', 1, SHA_B)]
        result = domain.compare(before, after)
        self.assertEqual(result['renamed'],
                         [{'from': 'old/name', 'to': 'new/name'}])
        self.assertEqual(result['added'], [])
        self.assertEqual(result['removed'], [])
        self.assertEqual(result['unchanged'], ['keep'])

    def test_ambiguous_signature_no_greedy_pairing(self):
        """Two old and two new paths sharing one signature stay added/removed."""
        before = [entry('o1', 7, SHA_A), entry('o2', 7, SHA_A),
                  entry('solo_old', 8, SHA_A)]
        after = [entry('n1', 7, SHA_A), entry('n2', 7, SHA_A),
                 entry('solo_new', 8, SHA_A)]
        result = domain.compare(before, after)
        self.assertEqual(result['renamed'], [{'from': 'solo_old', 'to': 'solo_new'}])
        self.assertEqual(result['added'], ['n1', 'n2'])
        self.assertEqual(result['removed'], ['o1', 'o2'])

    def test_shared_paths_never_renamed(self):
        """Shared paths are bucketed first and never paired as renames.

        Even when a shared path repeats the signature of an unmatched pair,
        only the unmatched old/new paths get paired.
        """
        before = [entry('shared', 5, SHA_A), entry('gone', 5, SHA_A)]
        after = [entry('shared', 5, SHA_A), entry('arrived', 5, SHA_A)]
        result = domain.compare(before, after)
        self.assertEqual(result['unchanged'], ['shared'])
        self.assertEqual(result['renamed'],
                         [{'from': 'gone', 'to': 'arrived'}])
        self.assertEqual(result['added'], [])
        self.assertEqual(result['removed'], [])
        # A modified shared path stays in modified, never in renamed.
        mod = domain.compare([entry('shared', 1, SHA_A)],
                             [entry('shared', 2, SHA_A)])
        self.assertEqual(mod['renamed'], [])
        self.assertEqual(mod['modified'],
                         [{'path': 'shared', 'before_size': 1,
                           'after_size': 2}])


class ValidationRejection(unittest.TestCase):
    def test_invalid_entries_raise_valueerror(self):
        """Malformed manifests are rejected with ValueError."""
        bad = [
            entry('a', True, SHA_A),            # bool size
            entry('a', 1.0, SHA_A),             # float size
            entry('a', -1, SHA_A),              # negative size
            entry('a', 1000001, SHA_A),         # size too large
            entry('a', 1, 'A' * 64),            # uppercase hash
            entry('a', 1, 'ab' * 31),           # 62 chars
            entry('', 1, SHA_A),                # empty path
            entry('.', 1, SHA_A),               # dot segment
            entry('a/../b', 1, SHA_A),          # dotdot segment
            entry('/abs', 1, SHA_A),            # absolute
            entry('a/', 1, SHA_A),              # trailing slash
            entry('a//b', 1, SHA_A),           # repeated slash
            entry('a\\b', 1, SHA_A),           # backslash
            entry('a/b' + 'c' * 120, 1, SHA_A), # path too long
            entry('a b', 1, SHA_A),            # space not allowed
            {'path': 'a', 'size': 1},           # missing key
            {'path': 'a', 'size': 1, 'sha256': SHA_A, 'extra': 1},  # extra key
            ['a', 1, SHA_A],                   # not an object
        ]
        for item in bad:
            with self.assertRaises(ValueError):
                validation.entries([item])
        with self.assertRaises(ValueError):
            validation.entries([entry('dup', 1, SHA_A), entry('dup', 2, SHA_B)])
        with self.assertRaises(ValueError):
            validation.entries([entry('p%d' % i, i, SHA_A) for i in range(101)])
        with self.assertRaises(ValueError):
            validation.entries('not a list')

    def test_inputs_never_mutated(self):
        """Neither success nor failure may mutate the caller's data."""
        before = [entry('x', 1, SHA_A)]
        after = [entry('y', 2, SHA_B)]
        domain.compare(before, after)
        self.assertEqual(before, [entry('x', 1, SHA_A)])
        self.assertEqual(after, [entry('y', 2, SHA_B)])
        # A failing validation leaves the (partially bad) input untouched.
        broken = [entry('ok', 1, SHA_A), {'bad': True}]
        for manifest in (broken, broken):
            try:
                validation.entries(manifest)
            except ValueError:
                pass
        self.assertEqual(broken, [entry('ok', 1, SHA_A), {'bad': True}])

    def test_totals_and_delta(self):
        """report.totals sums every entry, including removed/added ones."""
        before = [entry('x', 100, SHA_A), entry('gone', 7, SHA_B)]
        after = [entry('x', 100, SHA_A), entry('new', 3, SHA_C)]
        self.assertEqual(report.totals(before, after),
                         {'before_bytes': 107, 'after_bytes': 103,
                          'delta_bytes': -4})
        self.assertEqual(report.totals([], []),
                         {'before_bytes': 0, 'after_bytes': 0, 'delta_bytes': 0})


class ApiSurface(unittest.TestCase):
    def test_ping_and_compare_payloads(self):
        """Baseline ping is preserved; compare gains a summary."""
        self.assertEqual(api.run({'action': 'ping'}), {'ok': True})
        payload = {'action': 'compare',
                   'before': [entry('x', 1, SHA_A)],
                   'after': [entry('y', 1, SHA_A)]}
        result = api.run(payload)
        self.assertEqual(result['renamed'], [{'from': 'x', 'to': 'y'}])
        self.assertEqual(result['summary'],
                         {'before_bytes': 1, 'after_bytes': 1, 'delta_bytes': 0})

    def test_bad_payloads_raise(self):
        """Unknown actions, extra/missing fields and non-objects are rejected."""
        for payload in [{'action': 'nope'}, {}, {'action': 'ping', 'x': 1},
                        {'action': 'compare', 'before': []},
                        {'action': 'compare', 'before': [], 'after': [], 'z': 1},
                        'not-an-object', {'action': 'compare', 'before': 'x',
                                          'after': []}]:
            with self.assertRaises(ValueError):
                api.run(payload)


class CliBehavior(unittest.TestCase):
    def _run_cli(self, stdin_text):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'main.py')],
                              input=stdin_text, capture_output=True,
                              text=True, cwd='/tmp', timeout=30)
        return proc.returncode, proc.stdout.strip(), proc.stderr

    def test_cli_success_and_errors(self):
        """Exit 0 with only the JSON result; exit 2 with the fixed error."""
        payload = json.dumps({'action': 'ping'})
        code, out, err = self._run_cli(payload)
        self.assertEqual((code, out, err), (0, '{"ok": true}', ''))
        code, out, err = self._run_cli('{not json')
        self.assertEqual((code, out, err),
                         (2, '{"error": "invalid input"}', ''))
        code, out, err = self._run_cli(json.dumps({'action': 'boom'}))
        self.assertEqual((code, out, err),
                         (2, '{"error": "invalid input"}', ''))
        code, out, err = self._run_cli(json.dumps(
            {'action': 'compare', 'before': [entry('a', 1, SHA_A)],
             'after': []}))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)['removed'], ['a'])


if __name__ == '__main__':
    unittest.main()
