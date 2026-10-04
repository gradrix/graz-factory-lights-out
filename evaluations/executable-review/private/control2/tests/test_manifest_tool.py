"""Regression tests for the manifest tool (A1-A6).

Run from the project root: python -m unittest discover -s /workspace
"""
import copy
import unittest
import json
import subprocess
import sys
from pathlib import Path

from manifest_tool import api, domain, report
from manifest_tool.validation import entries

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def sha(letter, n=64):
    return letter * n


class CompareBehaviorTestCase(unittest.TestCase):
    """Ordinary compare behaviour: added/removed/modified/unchanged/renamed."""

    def test_shared_paths_and_summary(self):
        before = [
            {"path": "src/a.py", "size": 10, "sha256": sha("a")},
            {"path": "src/b.py", "size": 20, "sha256": sha("b")},
            {"path": "keep.txt", "size": 3, "sha256": sha("c")},
            {"path": "gone.txt", "size": 7, "sha256": sha("d")},
        ]
        after = [
            {"path": "src/a.py", "size": 11, "sha256": sha("a")},
            {"path": "src/b.py", "size": 20, "sha256": sha("b")},
            {"path": "keep.txt", "size": 3, "sha256": sha("c")},
            {"path": "new.txt", "size": 5, "sha256": sha("e")},
        ]
        before_copy, after_copy = copy.deepcopy(before), copy.deepcopy(after)
        result = domain.compare(before, after)
        self.assertEqual(
            set(result), {"added", "removed", "modified", "renamed", "unchanged"}
        )
        self.assertEqual(result["added"], ["new.txt"])
        self.assertEqual(result["removed"], ["gone.txt"])
        self.assertEqual(
            result["modified"],
            [{"path": "src/a.py", "before_size": 10, "after_size": 11}],
        )
        self.assertEqual(result["unchanged"], ["keep.txt", "src/b.py"])
        self.assertEqual(result["renamed"], [])
        summary = report.totals(before, after)
        self.assertEqual(
            summary,
            {"before_bytes": 40, "after_bytes": 39, "delta_bytes": -1},
        )
        api_result = api.run({"action": "compare", "before": before, "after": after})
        self.assertEqual({k: v for k, v in api_result.items() if k != "summary"}, result)
        self.assertEqual(api_result["summary"], summary)
        self.assertEqual((before, after), (before_copy, after_copy))

    def test_rename_detection(self):
        before = [
            {"path": "old/name.txt", "size": 4, "sha256": sha("f")},
            {"path": "shared.txt", "size": 1, "sha256": sha("0")},
        ]
        after = [
            {"path": "new/name.txt", "size": 4, "sha256": sha("f")},
            {"path": "shared.txt", "size": 1, "sha256": sha("0")},
        ]
        result = domain.compare(before, after)
        self.assertEqual(result["renamed"], [{"from": "old/name.txt", "to": "new/name.txt"}])
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["unchanged"], ["shared.txt"])
        self.assertEqual(result["modified"], [])

    def test_renamed_sorts_by_from(self):
        before = [
            {"path": "z/one", "size": 1, "sha256": sha("1")},
            {"path": "a/two", "size": 2, "sha256": sha("2")},
        ]
        after = [
            {"path": "z/two", "size": 2, "sha256": sha("2")},
            {"path": "a/one", "size": 1, "sha256": sha("1")},
        ]
        result = domain.compare(before, after)
        self.assertEqual(
            result["renamed"],
            [{"from": "a/two", "to": "z/two"}, {"from": "z/one", "to": "a/one"}],
        )
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])


class RenameEdgeCasesTestCase(unittest.TestCase):
    """Ambiguous signatures, shared paths, empty manifests, input order."""

    def test_ambiguous_signature_is_not_paired(self):
        before = [
            {"path": "dup/one", "size": 9, "sha256": sha("9")},
            {"path": "dup/two", "size": 9, "sha256": sha("9")},
        ]
        after = [{"path": "dup/three", "size": 9, "sha256": sha("9")}]
        result = domain.compare(before, after)
        self.assertEqual(result["renamed"], [])
        self.assertEqual(result["removed"], ["dup/one", "dup/two"])
        self.assertEqual(result["added"], ["dup/three"])

    def test_shared_paths_never_rename(self):
        # The shared path keeps the signature of an unmatched new path, but a
        # shared path is never a rename source/target: no unmatched old path
        # exists, so the new path is a plain addition.
        before = [
            {"path": "same.txt", "size": 4, "sha256": sha("a")},
            {"path": "gone.txt", "size": 8, "sha256": sha("c")},
        ]
        after = [
            {"path": "same.txt", "size": 5, "sha256": sha("b")},
            {"path": "moved.txt", "size": 4, "sha256": sha("a")},
        ]
        result = domain.compare(before, after)
        # same.txt is shared, so its (4, sha a) signature cannot pair with
        # moved.txt; gone.txt has a different signature and stays removed.
        self.assertEqual(result["renamed"], [])
        self.assertEqual(result["removed"], ["gone.txt"])
        self.assertEqual(result["added"], ["moved.txt"])
        self.assertEqual(
            result["modified"], [{"path": "same.txt", "before_size": 4, "after_size": 5}]
        )
        self.assertEqual(result["unchanged"], [])

    def test_shared_signature_yields_no_rename_without_old_path(self):
        before = [{"path": "same.txt", "size": 4, "sha256": sha("a")}]
        after = [
            {"path": "same.txt", "size": 5, "sha256": sha("b")},
            {"path": "moved.txt", "size": 4, "sha256": sha("a")},
        ]
        result = domain.compare(before, after)
        self.assertEqual(result["renamed"], [])
        self.assertEqual(result["added"], ["moved.txt"])
        self.assertEqual(result["removed"], [])
        self.assertEqual(
            result["modified"], [{"path": "same.txt", "before_size": 4, "after_size": 5}]
        )
        self.assertEqual(result["unchanged"], [])

    def test_empty_manifests(self):
        self.assertEqual(
            domain.compare([], []),
            {"added": [], "removed": [], "modified": [], "renamed": [], "unchanged": []},
        )
        self.assertEqual(
            report.totals([], []),
            {"before_bytes": 0, "after_bytes": 0, "delta_bytes": 0},
        )
        empty_before = []
        one = [{"path": "x", "size": 0, "sha256": sha("0")}]
        self.assertEqual(domain.compare(empty_before, one)["added"], ["x"])
        self.assertEqual(report.totals(empty_before, one)["delta_bytes"], 0)

    def test_input_order_does_not_change_matching(self):
        before = [
            {"path": "b/old", "size": 3, "sha256": sha("3")},
            {"path": "a/old", "size": 4, "sha256": sha("4")},
        ]
        after = [
            {"path": "q/new", "size": 4, "sha256": sha("4")},
            {"path": "p/new", "size": 3, "sha256": sha("3")},
        ]
        forward = domain.compare(before, after)
        backward = domain.compare(list(reversed(before)), list(reversed(after)))
        self.assertEqual(forward, backward)
        self.assertEqual(
            forward["renamed"],
            [{"from": "a/old", "to": "q/new"}, {"from": "b/old", "to": "p/new"}],
        )


class ValidationRejectionTestCase(unittest.TestCase):
    """Invalid payloads raise ValueError and never mutate the inputs."""

    def test_rejections(self):
        good = {"path": "dir/file.txt", "size": 1, "sha256": sha("a")}
        bad_entries = [
            {"path": "dir/file.txt", "size": True, "sha256": sha("a")},
            {"path": "dir/file.txt", "size": 1, "sha256": "A" * 64},
            {"path": "dir/../file.txt", "size": 1, "sha256": sha("a")},
            {"path": "./file", "size": 1, "sha256": sha("a")},
            {"path": "/abs", "size": 1, "sha256": sha("a")},
            {"path": "a//b", "size": 1, "sha256": sha("a")},
            {"path": "a\\b", "size": 1, "sha256": sha("a")},
            {"path": "a/", "size": 1, "sha256": sha("a")},
            {"path": "", "size": 1, "sha256": sha("a")},
            {"path": "x" * 121, "size": 1, "sha256": sha("a")},
            {"path": "dir/file.txt", "size": 1000001, "sha256": sha("a")},
            {"path": "dir/file.txt", "size": -1, "sha256": sha("a")},
            {"path": "dir/file.txt", "size": 1},
            {"path": "dir/file.txt", "size": 1, "sha256": sha("a"), "extra": 1},
            {"path": "dir/\u00e9", "size": 1, "sha256": sha("a")},
        ]
        for bad in bad_entries:
            payload = [good, bad]
            snapshot = copy.deepcopy(payload)
            with self.assertRaises(ValueError):
                entries(payload)
            self.assertEqual(payload, snapshot)
        too_many = [
            {"path": "f%d" % i, "size": 0, "sha256": sha("a")} for i in range(101)
        ]
        with self.assertRaises(ValueError):
            entries(too_many)
        with self.assertRaises(ValueError):
            entries({"path": "f", "size": 0, "sha256": sha("a")})
        duplicate = [good, dict(good, path="dir/file.txt")]
        with self.assertRaises(ValueError):
            entries(duplicate)

    def test_api_rejections(self):
        good = {"path": "dir/file.txt", "size": 1, "sha256": sha("a")}
        bad_payloads = [
            {"action": "ping", "extra": 1},
            {"action": "compare", "before": [good]},
            {"action": "compare", "before": [good], "after": [good], "extra": 1},
            {"action": "diff", "before": [good], "after": [good]},
            {"action": "compare", "before": [{"path": ".."}], "after": []},
            {"action": "compare", "before": "not-a-list", "after": []},
            {"before": [], "after": []},
            [],
            "ping",
            None,
        ]
        for payload in bad_payloads:
            snapshot = copy.deepcopy(payload)
            with self.assertRaises(ValueError):
                api.run(payload)
            self.assertEqual(payload, snapshot)
        self.assertEqual(api.run({"action": "ping"}), {"ok": True})

    def test_cli_rejects_bad_stdin(self):
        cases = [
            ("not json at all", 2),
            ("", 2),
            ('{"action": "nope"}', 2),
            ('{"action": "ping", "junk": 1}', 2),
            ('{"action": "compare", "before": [{"path": "..", "size": 1, "sha256": "%s"}], "after": []}' % sha("a"), 2),
        ]
        for text, expected_code in cases:
            completed = subprocess.run(
                [sys.executable, str(MAIN)],
                input=text,
                capture_output=True,
                text=True,
                cwd="/tmp",
            )
            self.assertEqual(completed.returncode, expected_code)
            self.assertEqual(completed.stdout.strip(), '{"error":"invalid input"}')
            self.assertEqual(completed.stderr, "")

    def test_cli_success_output(self):
        payload = {
            "action": "compare",
            "before": [{"path": "old/name", "size": 4, "sha256": sha("f")}],
            "after": [{"path": "new/name", "size": 4, "sha256": sha("f")}],
        }
        completed = subprocess.run(
            [sys.executable, str(MAIN)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd="/tmp",
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")
        parsed = json.loads(completed.stdout)
        self.assertEqual(
            parsed,
            {
                "added": [],
                "modified": [],
                "renamed": [{"from": "old/name", "to": "new/name"}],
                "removed": [],
                "summary": {"before_bytes": 4, "after_bytes": 4, "delta_bytes": 0},
                "unchanged": [],
            },
        )


if __name__ == "__main__":
    unittest.main()
