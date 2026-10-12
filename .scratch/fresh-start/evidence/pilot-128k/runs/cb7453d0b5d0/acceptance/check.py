import json
from pathlib import Path
import subprocess
import tempfile
import unittest

DATA = '\n{"service":" api ","level":"info"}\nnot json\n{"service":"jobs","level":" WARN "}\n{"service":"api","level":"debug"}\n[]\n{"service":"","level":"INFO"}\n'


class LogAcceptance(unittest.TestCase):
    def run_cli(self, *args, text=None):
        return subprocess.run(['python', 'log_summary.py', *args], input=text, capture_output=True, text=True)

    def test_stdin_and_file(self):
        expected = {'total': 3, 'invalid': 3, 'by_service': {'api': 2, 'jobs': 1}, 'by_level': {'INFO': 1, 'WARN': 1, 'DEBUG': 1}}
        stdin = self.run_cli('-', text=DATA)
        self.assertEqual(stdin.returncode, 0, stdin.stderr)
        self.assertEqual(json.loads(stdin.stdout), expected)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'logs.jsonl'
            path.write_text(DATA)
            self.assertEqual(json.loads(self.run_cli(str(path)).stdout), expected)

    def test_strict_line_number(self):
        result = self.run_cli('-', '--strict', text=DATA)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('3', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_empty_and_missing(self):
        self.assertEqual(json.loads(self.run_cli('-', text='\n').stdout), {'total': 0, 'invalid': 0, 'by_service': {}, 'by_level': {}})
        result = self.run_cli('/missing/log-file.jsonl')
        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr)
        self.assertNotIn('Traceback', result.stderr)


unittest.main()
