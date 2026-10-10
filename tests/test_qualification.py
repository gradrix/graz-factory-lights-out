"""Qualification must establish its execution target before consuming model work."""
import json
from pathlib import Path
import tempfile
import unittest

from docker_support import requires_docker
from unittest.mock import patch

from ops.qualify_coding import environment_check, main
from gflo.sandbox import DEFAULT_IMAGE, Sandbox


class QualificationTests(unittest.TestCase):
    @requires_docker
    def test_executed_runtime_can_match_and_wrong_image_identity_cannot(self):
        sandbox = Sandbox()
        first = environment_check(sandbox)
        self.assertTrue(first['passed'], first)
        target = {key: first['observed'][key] for key in ('image', 'version', 'implementation')}
        self.assertTrue(environment_check(sandbox, target)['passed'])
        target['image'] = 'sha256:' + '0' * 64
        wrong = environment_check(sandbox, target)
        self.assertFalse(wrong['passed'])
        self.assertIn('image', wrong['error'])

    def test_existing_qualification_evidence_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = root / 'qualification.json'
            saved.write_text('{"preserve":true}')
            with patch('sys.argv', ['qualify_coding', 'unused-fixtures', str(root)]), \
                    patch('ops.qualify_coding.environment_check') as probe:
                with self.assertRaisesRegex(ValueError, 'never overwritten'):
                    main()
                probe.assert_not_called()
            self.assertEqual(saved.read_text(), '{"preserve":true}')

    @requires_docker
    def test_runtime_mismatch_is_recorded_before_any_model_or_task_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = root / 'fixtures'
            fixtures.mkdir()
            (fixtures / 'manifest.json').write_text(json.dumps({
                'sha256': {}, 'environment': {
                    'image': DEFAULT_IMAGE, 'version': '0.0.0', 'implementation': 'CPython'}}))
            config = root / 'config.json'
            config.write_text(json.dumps({'image': DEFAULT_IMAGE}))
            state = root / 'state'
            with patch('sys.argv', ['qualify_coding', str(fixtures), str(state), '--config', str(config)]), \
                    patch('ops.qualify_coding.ModelWorker') as model, \
                    patch('ops.qualify_coding.Factory') as factory:
                self.assertEqual(main(), 2)
                model.assert_not_called()
                factory.assert_not_called()
            receipt = json.loads((state / 'environment.json').read_text())
            self.assertFalse(receipt['passed'])
            self.assertEqual(receipt['observed']['image'], DEFAULT_IMAGE)
            self.assertNotEqual(receipt['observed']['version'], '0.0.0')
            self.assertIn('version', receipt['error'])
            self.assertEqual(receipt['check']['exit_code'], 0)


if __name__ == '__main__':
    unittest.main()
