import os
import pathlib
import subprocess
import sys
import tempfile
import tomllib

meta=tomllib.loads(pathlib.Path('pyproject.toml').read_text())
assert meta['build-system']['build-backend']=='setuptools.build_meta'
assert set(meta['build-system']['requires'])=={'setuptools','wheel'}
assert meta['project']['name']=='importflow-local' and meta['project']['version']=='0.1.0'
assert meta['project']['requires-python']=='>=3.11'
assert set(meta['project']['dependencies'])=={'fastapi==0.141.1','uvicorn==0.52.4'}
assert meta['project']['scripts']=={'importflow-api':'api:main','importflow-worker':'worker:main'}
assert set(meta['tool']['setuptools']['py-modules'])=={'blobs','tabular','jobs','worker','api'}
with tempfile.TemporaryDirectory() as folder:
    target=pathlib.Path(folder)/'installed'
    result=subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-build-isolation','--target',str(target),'.'],text=True,capture_output=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    env=dict(os.environ,PYTHONPATH=str(target))
    for entry in ('importflow-api','importflow-worker'):
        result=subprocess.run([sys.executable,str(target/'bin'/entry),'--help'],cwd=folder,env=env,text=True,capture_output=True)
        assert result.returncode==0 and 'usage:' in result.stdout,(entry,result.stdout,result.stderr)
    result=subprocess.run([sys.executable,'-c','import api,jobs,worker,blobs,tabular; print(api.__file__)'],cwd=folder,env=env,text=True,capture_output=True)
    assert result.returncode==0 and str(target) in result.stdout,(result.stdout,result.stderr)
print('package-ok')
