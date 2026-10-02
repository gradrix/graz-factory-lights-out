import json
from pathlib import Path
import tempfile
import unittest

from gflo.environment import EnvironmentStore
from gflo.prepare import prepare, check


class PrepareTests(unittest.TestCase):
    def test_stdlib_preparation_records_actual_runtime_and_rechecks_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            store = EnvironmentStore(Path(directory) / 'store')
            environment = prepare(store, 'python-stdlib')
            self.assertEqual(environment.profile, 'python-stdlib')
            self.assertEqual(environment.runtime['python'], '3.12.13')
            receipt = json.loads((environment.dependencies.parent / 'receipt.json').read_text())
            self.assertEqual(receipt['checks']['executor']['host']['NetworkMode'], 'none')
            self.assertEqual(receipt['checks']['executor']['host']['Runtime'], 'runc')
            self.assertTrue(check(environment)['passed'])
            self.assertEqual(prepare(store, 'python-stdlib').id, environment.id)

    def test_unsupported_profile_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                prepare(EnvironmentStore(Path(directory) / 'store'), 'arbitrary')

    def test_cli_prepares_inspects_and_checks_without_model_configuration(self):
        from contextlib import redirect_stdout
        import io
        from gflo.__main__ import main
        with tempfile.TemporaryDirectory() as directory:
            args = ['--config', '/nonexistent/config.json', 'environment', '--store', str(Path(directory) / 'store')]
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(args + ['prepare', 'python-stdlib']), 0)
                identity = json.loads(output.getvalue())['id']
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(args + ['inspect', identity]), 0)
                self.assertEqual(json.loads(output.getvalue())['metadata']['runtime']['python'], '3.12.13')
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(args + ['check', identity, '--repeat', '2']), 0)
                self.assertEqual(len(json.loads(output.getvalue())['checks']), 2)

    def test_bound_sandbox_uses_frozen_image_and_rejects_tampering(self):
        from gflo.sandbox import Sandbox
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = EnvironmentStore(root / 'store')
            environment = prepare(store, 'python-stdlib')
            workspace = root / 'workspace'
            workspace.mkdir()
            sandbox = Sandbox('sha256:' + '0' * 64)
            sandbox.bind(environment)
            result = sandbox.execute(workspace, ['python', '-c', 'import platform; print(platform.python_version())'])
            self.assertEqual(result['exit_code'], 0, result)
            self.assertEqual(result['image'], environment.image)
            self.assertIn('3.12.13', result['output'])
            environment.dependencies.chmod(0o755)
            with self.assertRaisesRegex(ValueError, 'root changed'):
                sandbox.execute(workspace, ['true'])

    def test_python_api_prepares_locked_wheels_and_imports_offline(self):
        from gflo.sandbox import Sandbox
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = prepare(EnvironmentStore(root / 'store'), 'python-api')
            self.assertEqual(environment.runtime['fastapi'], '0.115.12')
            receipt = json.loads((environment.dependencies.parent / 'receipt.json').read_text())
            self.assertEqual(len(receipt['metadata']['artifacts']), 16)
            sandbox = Sandbox(); sandbox.bind(environment)
            workspace = root / 'workspace'; workspace.mkdir()
            result = sandbox.execute(workspace, ['python', '-c',
                'from fastapi import FastAPI; from fastapi.testclient import TestClient; a=FastAPI(); a.get("/")(lambda: {"ok":True}); assert TestClient(a).get("/").json()=={"ok":True}'])
            self.assertEqual(result['exit_code'], 0, result)

    def test_node_typescript_prepares_locked_packages_and_compiles_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = prepare(EnvironmentStore(Path(directory) / 'store'), 'node-ts')
            self.assertEqual(environment.runtime['node'], 'v22.23.3')
            self.assertEqual(environment.runtime['typescript'], '5.8.3')
            self.assertTrue(check(environment)['passed'])
            receipt = json.loads((environment.dependencies.parent / 'receipt.json').read_text())
            self.assertEqual(len(receipt['metadata']['artifacts']), 3)

    def test_project_manifests_must_match_supported_recipe(self):
        from gflo.prepare import validate_project
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'project'
            shutil.copytree('evaluations/environment-coding/python-api/source', project)
            store = EnvironmentStore(root / 'store')
            facts = validate_project(store, 'python-api', project)
            self.assertIn('pyproject.toml', facts)
            path = project / 'pyproject.toml'
            path.write_text(path.read_text().replace('fastapi==0.115.12', 'fastapi==999'))
            with self.assertRaisesRegex(ValueError, 'Supported dependencies'):
                validate_project(store, 'python-api', project)
            with self.assertRaisesRegex(ValueError, 'stdlib'):
                validate_project(store, 'python-stdlib', project)

    def test_profile_selection_uses_manifest_kind(self):
        from gflo.prepare import infer_profile
        for profile in ('python-stdlib', 'python-api', 'node-ts'):
            self.assertEqual(infer_profile(Path('evaluations/environment-coding') / profile / 'source'), profile)
