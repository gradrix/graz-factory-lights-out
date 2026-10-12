"""Regression tests for log_summary.py (run with: python -m unittest tests.test_log_summary)."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import log_summary


class TestSummarize(unittest.TestCase):
    def test_counts_valid_records_with_trimming_and_uppercasing(self):
        lines = [
            '{"service": " alpha ", "level": " info "}\n',
            '{"service": "beta", "level": "warn"}\n',
            '{"service": "beta", "level": "error"}\n',
        ]
        summary = log_summary.summarize(lines)
        self.assertEqual(
            summary,
            {
                "total": 3,
                "invalid": 0,
                "by_service": {"alpha": 1, "beta": 2},
                "by_level": {"INFO": 1, "WARN": 1, "ERROR": 1},
            },
        )

    def test_blank_lines_are_ignored_and_invalid_records_counted(self):
        lines = [
            '{"service": "a", "level": "x"}\n',
            "\n",
            "   \n",
            "not json\n",
            '{"service": "", "level": "x"}\n',
            '{"level": "x"}\n',
            '{"service": "a", "level": 3}\n',
            '["service", "level"]\n',
            '{"service": "b", "level": " y "}\n',
        ]
        summary = log_summary.summarize(lines)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["invalid"], 5)
        self.assertEqual(summary["by_service"], {"a": 1, "b": 1})
        self.assertEqual(summary["by_level"], {"X": 1, "Y": 1})

    def test_strict_mode_raises_on_first_invalid_record_with_line_number(self):
        lines = io.StringIO(
            '{"service": "a", "level": "x"}\n'
            "\n"
            "oops\n"
            '{"service": "b", "level": "y"}\n'
        )
        with self.assertRaises(ValueError) as cm:
            log_summary.summarize(lines, strict=True)
        message = str(cm.exception)
        self.assertIn("line 3", message)

    def test_strict_mode_accepts_all_valid_input(self):
        lines = ['{"service": "s", "level": "any name"}\n']
        summary = log_summary.summarize(lines, strict=True)
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["by_level"], {"ANY NAME": 1})


class TestCli(unittest.TestCase):
    def run_cli(self, args, stdin=None):
        proc = subprocess.run(
            [sys.executable,
             os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "log_summary.py")] + args,
            input=stdin,
            capture_output=True,
            text=True,
        )
        return proc

    def test_cli_summary_on_file(self):
        tmpdir = tempfile.TemporaryDirectory()
        path = os.path.join(tmpdir.name, "sample.jsonl")
        try:
            with open(path, "w") as fh:
                fh.write('{"service": "svc", "level": "info"}\n')
                fh.write('garbage\n')
            proc = self.run_cli([path])
        finally:
            tmpdir.cleanup()
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            json.loads(proc.stdout),
            {"total": 1, "invalid": 1, "by_service": {"svc": 1}, "by_level": {"INFO": 1}},
        )
        self.assertEqual(proc.stderr, "")

    def test_cli_stdin_dash(self):
        proc = self.run_cli(["-"], stdin='{"service": "s", "level": "debug"}\n')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            json.loads(proc.stdout),
            {"total": 1, "invalid": 0, "by_service": {"s": 1}, "by_level": {"DEBUG": 1}},
        )

    def test_cli_strict_first_invalid_exits_2_with_line_error(self):
        proc = self.run_cli(["--strict", "-"],
                            stdin='{"service": "a", "level": "x"}\nbad line\n')
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("line 2", proc.stderr)

    def test_cli_missing_file_exits_2_with_clear_stderr(self):
        proc = self.run_cli(["/definitely/not/a/real/file.jsonl"])
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("cannot open", proc.stderr)


if __name__ == "__main__":
    unittest.main()
