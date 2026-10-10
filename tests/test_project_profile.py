import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from docker_support import requires_docker

from gflo.environment import EnvironmentStore, PROJECT_LIMITS, command_seconds, limits_for, runtime_context
from gflo.prepare import prepare, validate_project
from gflo.sandbox import Sandbox

spec = importlib.util.spec_from_file_location('resolver', Path(__file__).parents[1] / 'gflo/recipes/python-project/resolve.py')
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


class ResolverParsingTests(unittest.TestCase):
    def project(self, files):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        for name, text in files.items():
            (Path(directory.name) / name).write_text(text)
        return directory.name

    def test_pyproject_runtime_and_optional_dependencies_without_self_extra(self):
        root = self.project({'pyproject.toml': '[project]\nname = "coach_app"\ndependencies = ["pandas>=2.2,<3", "uvicorn[standard]>=0.34"]\n'
                                               '[project.optional-dependencies]\ndev = ["pytest==8.4.2"]\nall = ["coach-app[dev]"]\n'})
        self.assertEqual(resolver.requirements(root), ['pandas>=2.2,<3', 'pytest==8.4.2', 'uvicorn[standard]>=0.34'])

    def test_requirements_files_merge_and_skip_comments(self):
        root = self.project({'requirements.txt': '# runtime\nrequests==2.32.3  # pinned\n\n',
                             'requirements-test.txt': 'pytest==8.*\nrequests==2.32.3\n'})
        self.assertEqual(resolver.requirements(root), ['pytest==8.*', 'requests==2.32.3'])

    def test_constraints_choose_versions_and_pytest_is_always_installed(self):
        root = self.project({'pyproject.toml': '[project]\nname = "x"\ndependencies = ["sqlalchemy>=2,<3"]\n',
                             'constraints-runtime.txt': 'sqlalchemy==2.0.49\npytest==8.3.5\n'})
        self.assertEqual(resolver.constraints(root), ['pytest==8.3.5', 'sqlalchemy==2.0.49'])
        self.assertEqual(resolver.requested(root), ['sqlalchemy>=2,<3', 'pytest'])  # constraint pins it
        plain = self.project({'requirements.txt': 'pytest-asyncio==0.26.0\n'})
        self.assertEqual(resolver.requested(plain), ['pytest-asyncio==0.26.0', 'pytest'])
        named = self.project({'requirements.txt': 'PyTest==8.4.2\n'})
        self.assertEqual(resolver.requested(named), ['PyTest==8.4.2'])

    def test_uv_lock_registry_packages_become_constraints(self):
        root = self.project({'pyproject.toml': '[project]\nname = "app"\ndependencies = ["sqlalchemy>=2"]\n',
                             'uv.lock': 'version = 1\n[[package]]\nname = "sqlalchemy"\nversion = "2.0.36"\n'
                                        'source = { registry = "https://pypi.org/simple" }\n'
                                        '[[package]]\nname = "app"\nversion = "0.1.0"\nsource = { editable = "." }\n'})
        self.assertEqual(resolver.constraints(root), ['sqlalchemy==2.0.36'])
        self.assertEqual(resolver.requested(root), ['sqlalchemy>=2', 'pytest'])

    def test_uv_lock_keeps_the_version_resolved_for_this_interpreter(self):
        entry = ('[[package]]\nname = "numpy"\nversion = "{0}"\nsource = {{ registry = "https://pypi.org/simple" }}\n'
                 'resolution-markers = [{1}]\n')
        root = self.project({'requirements.txt': 'numpy\n', 'uv.lock': entry.format('2.2.6', '"python_full_version < \'3.11\'"')
                             + entry.format('2.5.2', '"python_full_version >= \'3.13\'", "python_full_version == \'3.12.*\'"')})
        self.assertEqual(resolver.constraints(root), ['numpy==2.5.2'])  # the check container is CPython 3.12

    def test_stale_lock_pin_yields_to_the_declared_requirement(self):
        root = self.project({'pyproject.toml': '[project]\nname = "app"\ndependencies = ["garminconnect==0.3.13", "sqlalchemy>=2,<3"]\n',
                             'uv.lock': ''.join(f'[[package]]\nname = "{name}"\nversion = "{version}"\n'
                                                'source = { registry = "https://pypi.org/simple" }\n'
                                                for name, version in [('garminconnect', '0.3.1'), ('sqlalchemy', '2.0.36'), ('greenlet', '3.1.1')])})
        kept, dropped = resolver.effective_constraints(root)
        self.assertEqual(kept, ['greenlet==3.1.1', 'sqlalchemy==2.0.36'])
        self.assertEqual(dropped, ['garminconnect==0.3.1'])

    def test_markers_and_normalized_self_reference(self):
        root = self.project({'pyproject.toml': '[project]\nname = "a.b"\ndependencies = ["tomli; python_version < \\"3.11\\""]\n'
                                               '[project.optional-dependencies]\nall = ["A_B[x]", "a-b>=1"]\n'})
        self.assertEqual(resolver.requirements(root), ['tomli; python_version < "3.11"'])

    def test_unsupported_declarations_fail_instead_of_resolving_nothing(self):
        with self.assertRaisesRegex(ValueError, r'no \[project\] table'):
            resolver.requirements(self.project({'pyproject.toml': '[tool.poetry.dependencies]\nrequests = "^2"\n'}))
        with self.assertRaisesRegex(ValueError, 'must be strings'):
            resolver.requirements(self.project({'pyproject.toml': '[project]\nname="x"\ndependencies=[{name="requests"}]\n'}))
        poetry_with_text = self.project({'pyproject.toml': '[tool.poetry]\n', 'requirements.txt': 'requests==2.32.3\n'})
        self.assertEqual(resolver.requirements(poetry_with_text), ['requests==2.32.3'])

    def test_urls_paths_options_and_includes_are_rejected(self):
        for line in ['git+https://example.com/x.git', 'pkg @ https://example.com/p.whl', '-e .', '-r other.txt',
                     'requests==2.32.3 --hash=sha256:abc', 'pkg --config-settings x=y', 'pkg --trusted-host evil',
                     '--index-url https://mirror/simple', './local', '/abs/path', 'C:\\pkg']:
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, 'only named PyPI requirements'):
                resolver.requirements(self.project({'requirements.txt': line + '\n'}))

    def test_missing_declarations_and_dynamic_dependencies_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'needs pyproject.toml'):
            resolver.requirements(self.project({'README.md': 'x'}))
        with self.assertRaisesRegex(ValueError, 'dynamic'):
            resolver.requirements(self.project({'pyproject.toml': '[project]\nname="x"\ndynamic=["dependencies"]\n'}))


class ProjectProfileTests(unittest.TestCase):
    def test_project_profile_has_larger_bounds_and_others_keep_defaults(self):
        self.assertIs(limits_for('python-project'), PROJECT_LIMITS)
        self.assertEqual(limits_for('python-api').entries, 16384)
        self.assertGreater(PROJECT_LIMITS.expanded_bytes, limits_for('python-stdlib').expanded_bytes)

    def test_project_commands_get_longer_than_fixture_commands(self):
        self.assertEqual(command_seconds({'environment': {'profile': 'python-project'}}), 300)
        self.assertEqual(command_seconds({'environment': {'profile': 'python-stdlib'}}), 60)
        self.assertEqual(command_seconds({'environment': None}), 60)

    def test_store_readers_wait_for_a_publication_instead_of_failing(self):
        import threading, time
        with tempfile.TemporaryDirectory() as directory:
            store = EnvironmentStore(Path(directory) / 'store')
            held = threading.Event()
            def publisher():
                with store.locked():
                    held.set()
                    time.sleep(1.5)
            thread = threading.Thread(target=publisher)
            thread.start()
            held.wait()
            started = time.monotonic()
            with store.locked(shared=True):
                waited = time.monotonic() - started
            thread.join()
            self.assertGreater(waited, 1.0)
            with store.locked(), self.assertRaisesRegex(ValueError, 'owns this store'):
                with EnvironmentStore(store.root).locked(shared=True, wait=0):
                    pass

    def test_preparation_requires_the_project(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'pass its repository'):
                prepare(EnvironmentStore(Path(directory) / 'store'), 'python-project')

    def test_worker_context_names_pytest_and_no_installs(self):
        context = runtime_context({'environment': {'profile': 'python-project', 'image': 'sha256:' + '0' * 64, 'runtime': {}}})
        self.assertIn('python -m pytest', context)
        self.assertIn('Nothing can be installed', context)
        self.assertNotIn('Project test command', context)
        context = runtime_context({'environment': {'profile': 'python-project', 'image': 'sha256:' + '0' * 64, 'runtime': {}},
                                   'test_command': ['env', 'X=1', 'python', '-m', 'pytest', 'tests']})
        self.assertIn('Project test command (also run by acceptance): ["env", "X=1", "python", "-m", "pytest", "tests"]', context)

    @requires_docker
    def test_resolved_project_runs_pytest_offline_and_binds_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'project'
            (project / 'tests').mkdir(parents=True)
            (project / 'requirements.txt').write_text('iniconfig==2.1.0\n')
            (project / 'app.py').write_text('import iniconfig\n\ndef parse(text):\n    return iniconfig.IniConfig("x.ini", data=text)["s"]["k"]\n')
            (project / 'tests' / 'test_app.py').write_text('from app import parse\n\ndef test_parse():\n    assert parse("[s]\\nk = v\\n") == "v"\n')
            store = EnvironmentStore(root / 'store')
            hashes = validate_project(store, 'python-project', project)
            self.assertEqual(sorted(hashes), ['requirements.txt'])
            environment = prepare(store, 'python-project', project=project)
            self.assertEqual(environment.profile, 'python-project')
            self.assertRegex(environment.runtime['pytest'], r'^\d+\.')  # unpinned unless the project pins it
            lock = json.loads((environment.dependencies / 'gflo-lock.json').read_text())
            self.assertIn('iniconfig', {item['name'] for item in lock['resolved']})
            receipt = json.loads((environment.dependencies.parent / 'receipt.json').read_text())
            self.assertEqual(receipt['checks']['executor']['host']['NetworkMode'], 'none')
            sandbox = Sandbox()
            sandbox.bind(environment)
            acceptance = root / 'acceptance'
            acceptance.mkdir()
            task = {'checks': [], 'environment_inputs': hashes}
            result = sandbox.verify(project, task, acceptance)
            self.assertTrue(result['passed'], result)
            self.assertIn('pytest', result['checks'][-1]['command'])
            custom = dict(task, test_command=['env', 'MARK=1', 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-k', 'nothing_matches'])
            result = sandbox.verify(project, custom, acceptance)
            self.assertFalse(result['passed'])  # pytest exits 5 when the operator command selects no tests
            self.assertEqual(result['checks'][-1]['command'], custom['test_command'])
            suite = ['python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests']
            once = sandbox.verify(project, dict(task, checks=[suite], test_command=suite), acceptance)
            self.assertTrue(once['passed'], once)
            self.assertEqual([check['command'] for check in once['checks']], [suite])  # not run twice
            (project / 'constraints.txt').write_text('iniconfig==2.1.0\n')
            added = sandbox.verify(project, task, acceptance)
            self.assertFalse(added['passed'])
            self.assertIn('added after the environment was frozen: constraints.txt', added['checks'][0]['output'])
            (project / 'constraints.txt').unlink()
            (project / 'requirements.txt').write_text('iniconfig==2.0.0\n')
            self.assertFalse(sandbox.verify(project, task, acceptance)['passed'])
            # A receipt resolved from other manifests cannot bind a run of this commit.
            import subprocess
            from gflo.runner import Factory
            subprocess.run(['git', 'init', '-q', str(project)], check=True)
            subprocess.run(['git', '-C', str(project), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(project), '-c', 'user.name=T', '-c', 'user.email=t@local', 'commit', '-qm', 'base'], check=True)
            (acceptance / 'check.py').write_text('pass\n')
            task_file = root / 'task.json'
            task_file.write_text(json.dumps({'repo': str(project), 'objective': 'x', 'acceptance': str(acceptance),
                                             'checks': [['python', '/acceptance/check.py']], 'profile': 'python-project'}))
            factory = Factory(root / 'state', lambda *a: {}, sandbox.verify, environment=environment, bind_environment=sandbox.bind)
            with self.assertRaisesRegex(ValueError, 'different dependency manifests'):
                factory.create(task_file)
            self.assertEqual([path for path in (root / 'state').iterdir() if path.is_dir()], [])  # no orphan run


if __name__ == '__main__':
    unittest.main()
