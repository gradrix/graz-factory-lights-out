"""Exact regex termination and invalid UTF-8 boundaries found by source review."""
import json
import pathlib
import subprocess
import sys
import tempfile
import core

failures=[]
for name in ['a\n', 'a\r', 'a\r\n']:
    try:
        core.run(json.dumps({name: []}))
    except ValueError:
        pass
    else:
        failures.append(('invalid node name accepted', repr(name)))
if pathlib.Path('cli.py').exists():
    with tempfile.TemporaryDirectory() as folder:
        path=pathlib.Path(folder)/'bad.txt'
        path.write_bytes(b'\xff')
        result=subprocess.run([sys.executable,'-m','cli',str(path)],text=True,capture_output=True)
        if result.returncode != 2 or result.stdout or not result.stderr or 'Traceback' in result.stderr:
            failures.append(('invalid UTF-8 not handled',result.returncode,result.stdout,result.stderr))
assert not failures, failures
print('postreview-ok')
