NAME = 'dagorder'
VALID = ('{"z":[],"b":["a"],"a":[]}', ['a', 'b', 'z'])
import json, os, pathlib, subprocess, sys, tempfile, tomllib
meta = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
assert meta['build-system']['build-backend'] == 'setuptools.build_meta'
assert set(meta['build-system']['requires']) == {'setuptools', 'wheel'}
assert meta['project']['name'] == NAME+'-local' and meta['project']['version'] == '0.1.0'
assert meta['project']['requires-python'] == '>=3.11'
assert meta['project'].get('dependencies', []) == []
assert meta['project']['scripts'][NAME] == 'cli:main'
assert set(meta['tool']['setuptools']['py-modules']) == {'core', 'cli'}
with tempfile.TemporaryDirectory() as folder:
    target = pathlib.Path(folder)/'installed'
    proc = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-build-isolation', '--target', str(target), '.'], text=True, capture_output=True)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    path = pathlib.Path(folder)/'input.txt'
    path.write_text(VALID[0])
    env = dict(os.environ, PYTHONPATH=str(target))
    proc = subprocess.run([sys.executable, str(target/'bin'/NAME), str(path)], cwd=folder, env=env, text=True, capture_output=True)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert json.loads(proc.stdout) == VALID[1], proc.stdout
    probe = subprocess.run([sys.executable, '-c', 'import core; print(core.__file__)'], cwd=folder, env=env, text=True, capture_output=True)
    assert str(target) in probe.stdout, probe.stdout
print('package-ok')
