from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest

from docker_support import requires_docker
from unittest.mock import patch

from gflo.__main__ import main


class CliTests(unittest.TestCase):
    def test_status_needs_no_model_or_config(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['--state', directory, 'status']), 0)
            self.assertEqual(json.loads(output.getvalue()), [])

    def test_missing_config_is_actionable(self):
        with redirect_stderr(io.StringIO()) as output:
            self.assertEqual(main(['--config', '/nonexistent/config.json', 'doctor']), 1)
            self.assertIn('config.example.json', output.getvalue())

    @requires_docker
    def test_doctor_checks_image_and_model(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps({'endpoint': 'http://127.0.0.1:18000', 'model': 'example'}))
            with patch('gflo.__main__.ModelWorker.request', side_effect=[{'data': [{'id': 'example'}]}, {'default_generation_settings': {'n_ctx': 131072}}]), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(['--config', str(config), 'doctor']), 0)
                self.assertEqual(json.loads(output.getvalue())['context'], 131072)
            with patch('gflo.__main__.ModelWorker.request', return_value={'data': []}), redirect_stderr(io.StringIO()) as output:
                self.assertEqual(main(['--config', str(config), 'doctor']), 1)
                self.assertIn('not served', output.getvalue())
