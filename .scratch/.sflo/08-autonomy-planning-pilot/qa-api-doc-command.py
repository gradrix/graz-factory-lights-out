"""Focused paired check: documented bare uvicorn vs installed-module command."""
import argparse,json,os,pathlib,shutil,socket,subprocess,sys,tempfile,time,urllib.request
p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);a=p.parse_args()
assert sys.version_info[:3]==(3,12,13)
results=[]
with tempfile.TemporaryDirectory() as temporary:
 root=pathlib.Path(temporary);build=root/'build';shutil.copytree(a.project,build);wheels=root/'wheels';wheels.mkdir();site=root/'site';site.mkdir()
 env=dict(os.environ,PYTHONPATH='/opt/deps',PYTHONDONTWRITEBYTECODE='1',PIP_NO_INDEX='1')
 def run(argv,cwd):
  r=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,timeout=30);assert r.returncode==0,(r.returncode,r.stderr);return r
 run([sys.executable,'-c','import setuptools.build_meta as b;b.build_wheel('+repr(str(wheels))+')'],build)
 run([sys.executable,'-m','pip','install','--no-index','--no-deps','--target',str(site),str(next(wheels.glob('*.whl')))],root)
 env['PYTHONPATH']=str(site)+':/opt/deps'
 for label,prefix in [('documented_bare_uvicorn',['uvicorn']),('conforming_module_command',[sys.executable,'-m','uvicorn'])]:
  sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();process=None
  try:
   process=subprocess.Popen(prefix+['config_preview.app:app','--host','127.0.0.1','--port',str(port),'--log-level','error'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
   deadline=time.monotonic()+5
   while True:
    try:
     with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=1) as response: value=json.load(response)
     assert value=={'status':'ok'};break
    except OSError:
     if process.poll() is not None or time.monotonic()>deadline:raise
     time.sleep(.05)
   results.append({'label':label,'passed':True,'health':value})
  except Exception as error:results.append({'label':label,'passed':False,'type':type(error).__name__,'detail':str(error)[:1000]})
  finally:
   if process:
    process.terminate()
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
 print(json.dumps({'results':results,'bare_uvicorn_available':shutil.which('uvicorn')},indent=2))
