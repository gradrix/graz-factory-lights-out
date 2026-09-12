VALID = ('{"z":[],"b":["a"],"a":[]}', ['a', 'b', 'z'])
INVALID = '{"a":[],"b":[1]}'
import contextlib, io, json, os, pathlib, subprocess, sys, tempfile
import cli

def check(command, code, expected=None, error=False):
    proc = subprocess.run(command, text=True, capture_output=True)
    assert proc.returncode == code, (command, code, proc.returncode, proc.stdout, proc.stderr)
    assert 'Traceback' not in proc.stderr, proc.stderr
    if error:
        assert proc.stderr.strip() and not proc.stdout, (command, proc.stdout, proc.stderr)
    if expected is not None:
        assert json.loads(proc.stdout) == expected, (proc.stdout, expected)
    return proc
with tempfile.TemporaryDirectory() as folder:
    path = pathlib.Path(folder)/'input.txt'
    raw, expected = VALID
    path.write_text(raw, encoding='utf-8')
    check([sys.executable, '-m', 'cli', str(path)], 0, expected)
    assert path.read_text() == raw
    check([sys.executable, '-m', 'cli', '--help'], 0)
    check([sys.executable, '-m', 'cli'], 2, error=True)
    check([sys.executable, '-m', 'cli', str(path)+'missing'], 2, error=True)
    path.write_text(INVALID)
    check([sys.executable, '-m', 'cli', str(path)], 2, error=True)
    assert path.read_text() == INVALID
    for args, status in (([], 2), (['--help'], 0), ([str(path)], 2)):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            actual = cli.main(args)
        assert actual == status, (args, status, actual)
print('cli-ok')
