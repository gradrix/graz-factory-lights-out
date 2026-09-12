import pathlib, shutil, subprocess, sys, tempfile
source = pathlib.Path('core.py').read_text()
mutants = {
    'empty': '\ndef run(text):\n    return []\n',
    'reverse': '\n_original = run\ndef run(text):\n    return list(reversed(_original(text)))\n',
    'accept-invalid': '\n_original = run\ndef run(text):\n    try:\n        return _original(text)\n    except ValueError:\n        return []\n',
}
import ast
tree = ast.parse(pathlib.Path('tests/test_core.py').read_text())
assert len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]) >= 6, 'six tests required'
for name, suffix in [('correct', ''), *mutants.items()]:
    with tempfile.TemporaryDirectory() as folder:
        dest = pathlib.Path(folder)
        (dest/'core.py').write_text(source + suffix)
        shutil.copytree('tests', dest/'tests')
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'], cwd=dest, text=True, capture_output=True)
        assert (result.returncode == 0) if name == 'correct' else (result.returncode == 1), (name, result.returncode, result.stdout, result.stderr)
        assert 'skipped' not in result.stdout and 'xfailed' not in result.stdout, result.stdout
print('tests-ok')
