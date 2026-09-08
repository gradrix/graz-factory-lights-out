"""Fail-closed target checks and cleanup, without requiring Docker."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('check_target', Path(__file__).resolve().parents[1] / 'scripts/check_target.py')
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)


class TargetTests(unittest.TestCase):
    def test_absent_controls_cannot_pass(self):
        self.assertFalse(any(target.sandbox_checks({}).values()))

    def test_unlimited_cpu_cannot_pass(self):
        for value in ('max 100000', '0 0', '-1 100000', '200000 100000'):
            with self.subTest(value=value):
                self.assertFalse(target.sandbox_checks({'cpu_max': value})['cpu_limit'])

    def test_timeout_cleans_up_only_owned_probe(self):
        identity = json.dumps([{'Id': 'sha256:local', 'RepoDigests': []}])
        with patch.object(target, 'run', side_effect=[identity, subprocess.TimeoutExpired('docker', 45)]) as run:
            with patch.object(target.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as cleanup:
                with self.assertRaises(subprocess.TimeoutExpired):
                    target.container_probe('python:test', ['python', '-V'])
        command = run.call_args.args[0]
        name = command[command.index('--name') + 1]
        self.assertTrue(name.startswith('gflo-target-probe-'))
        self.assertIn('sha256:local', command)
        self.assertNotIn('python:test', command)
        self.assertEqual(cleanup.call_args.args[0], ['docker', 'rm', '-f', name])

    def test_cleanup_failure_is_not_success(self):
        identity = json.dumps([{'Id': 'sha256:local'}])
        with patch.object(target, 'run', side_effect=[identity, 'ok']):
            with patch.object(target.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, stderr='daemon unavailable')):
                with self.assertRaisesRegex(RuntimeError, 'cleanup failed'):
                    target.container_probe('python:test', ['python', '-V'])


if __name__ == '__main__':
    unittest.main()
