import subprocess,sys,pathlib,json,os,shutil
out=[]
def run(label,args,env=None,cwd='/tmp'):
 p=subprocess.run(args,capture_output=True,text=True,env=env,cwd=cwd,timeout=90);out.append(dict(label=label,command=args,cwd=cwd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));print(json.dumps(out),flush=True);return p
p=run('offline-dependencies',[sys.executable,'-m','pip','install','--no-index','--find-links','/wheels','--target','/tmp/deps','fastapi==0.115.12','uvicorn==0.34.2','pydantic==2.13.5','setuptools==78.1.0','httpx==0.28.1']);assert p.returncode==0,p.stderr
env=dict(os.environ,PYTHONPATH='/tmp/deps',PIP_NO_INDEX='1')
p=run('frozen-oracle',[sys.executable,'-B','/acceptance/check.py','/project with spaces'],env);assert p.returncode!=0 and 'new documentation required' in p.stderr
source=pathlib.Path('/acceptance/check.py').read_text();assert " and 'pip' in doc" in source
pathlib.Path('/tmp/check-without-pip.py').write_text(source.replace(" and 'pip' in doc",''))
p=run('diagnostic-oracle-without-literal-token',[sys.executable,'-B','/tmp/check-without-pip.py','/project with spaces'],env);assert p.returncode==0,p.stderr
# Install isolated final wheel for exact documented launch check.
shutil.copytree('/project with spaces','/tmp/project')
p=run('wheel-build',[sys.executable,'-m','pip','wheel','/tmp/project','--no-build-isolation','--no-deps','--no-index','--wheel-dir','/tmp/wheels'],env);assert p.returncode==0
wheel=str(next(pathlib.Path('/tmp/wheels').glob('*.whl')))
p=run('wheel-install',[sys.executable,'-m','pip','install','--no-index','--no-deps','--target','/tmp/installed',wheel],env);assert p.returncode==0
installed=dict(env,PYTHONPATH='/tmp/installed:/tmp/deps')
p=run('documented-uvicorn-import',[sys.executable,'-c',"from uvicorn.importer import import_from_string; from fastapi import FastAPI; assert isinstance(import_from_string('reservation_preview:app'),FastAPI)"],installed);assert p.returncode!=0
p=run('correct-uvicorn-import-control',[sys.executable,'-c',"from uvicorn.importer import import_from_string; from fastapi import FastAPI; assert isinstance(import_from_string('reservation_preview.app:app'),FastAPI); print('correct app import passes')"],installed);assert p.returncode==0
readme=pathlib.Path('/tmp/project/README.md');text=readme.read_text().replace('uvicorn reservation_preview:app','python -m uvicorn reservation_preview.app:app')
text+='\nOffline wheel install (use the already prepared profile dependencies):\n\n```sh\npython -m pip wheel . --no-index --no-deps --no-build-isolation --wheel-dir /tmp/reservation-wheels\npython -m pip install --no-index --no-deps /tmp/reservation-wheels/*.whl\npython -m uvicorn reservation_preview.app:app\n```\n'
readme.write_text(text)
p=run('disposable-readme-repair-original-oracle',[sys.executable,'-B','/acceptance/check.py','/tmp/project'],env);assert p.returncode==0,p.stderr
print(json.dumps(out))
