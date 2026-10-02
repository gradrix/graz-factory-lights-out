import sys,json,subprocess,threading,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
BASE=Path(__file__).resolve().parent

from qa_pinned import activate, evidence, INITIAL
activate(INITIAL)
from gflo.runner import Factory
from gflo.review import Reviewer
from gflo.worker import ModelWorker
from gflo.sandbox import Sandbox
ROOT=evidence('qa-evidence'); ROOT.mkdir(exist_ok=True)
repo=ROOT/'repo'; repo.mkdir(exist_ok=True); (repo/'app.py').write_text('value = 2\n')
for command in [['git','init','-q',str(repo)],['git','-C',str(repo),'add','.'],['git','-C',str(repo),'-c','user.name=QA','-c','user.email=qa@local','commit','-qm','fixture']]: subprocess.run(command,check=True)
accept=ROOT/'acceptance'; accept.mkdir(); (accept/'check.py').write_text("import pathlib\nassert pathlib.Path('/workspace/app.py').read_text() == 'value = 2\\n'\n")
task=ROOT/'task.json'; task.write_text(json.dumps(dict(repo=str(repo),acceptance=str(accept),objective='Set value to 2',checks=[['python','-I','/acceptance/check.py']],max_attempts=2)))
requests=[]; replies=[]
class HTTP(BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length']))); requests.append(body)
  reply=replies.pop(0); out=json.dumps({'choices':[{'message':{'content':json.dumps(reply)}}]}).encode(); self.send_response(200); self.end_headers(); self.wfile.write(out)
server=ThreadingHTTPServer(('127.0.0.1',0),HTTP); threading.Thread(target=server.serve_forever,daemon=True).start()
sandbox=Sandbox(); client=ModelWorker({'endpoint':f'http://127.0.0.1:{server.server_port}','model':'qa-fake'},sandbox); reviewer=Reviewer(client)
PASS={'decision':'pass','findings':[],'question':''}
MAJOR={'severity':'major','path':'app.py','line':1,'evidence':'Objective mismatch','repair':'Correct value'}
results=[]
def run(name, response, expected, adapter=False):
 replies.append(response) if not adapter else None
 f=Factory(ROOT/name,lambda *a:{},sandbox.verify,reviewer=(lambda *a:response) if adapter else reviewer); rid=f.create(task)
 try: actual=f.resume(rid)['status']
 except Exception as e: actual=f.status(rid)['status']; error=str(e)
 else: error=''
 results.append(dict(name=name,expected=expected,actual=actual,pass_=actual==expected,error=error,run=rid))
 return f,rid
run('valid',PASS,'accepted')
run('unknown',dict(PASS,decision='approve'),'interrupted')
run('missing',{'decision':'pass'},'interrupted')
run('blocking-pass',dict(PASS,findings=[MAJOR]),'interrupted')
run('question-pass',dict(PASS,question='Should the value be 3 instead?'),'interrupted')
run('adapter-malformed',{'decision':'pass'},'interrupted',True)
f,rid=run('needs-input',dict(PASS,decision='needs_input',question='Should the value be 3 instead?'),'needs_input')
results.append(dict(name='needs-input-resume',actual=f.resume(rid)['status'],attempts=f.status(rid)['attempts']))
f,rid=run('receipt',PASS,'accepted'); (f.state/rid/'attempts/1/review.json').unlink(); results.append(dict(name='missing-review-receipt',expected='invalidated',actual=f.status(rid)['status']))
replies.extend([dict(PASS,decision='repair',findings=[MAJOR]),PASS]); feedback=[]
f=Factory(ROOT/'lifecycle',lambda w,t,p,a: feedback.append(p) or {},sandbox.verify,reviewer=reviewer); rid=f.create(task); r=f.resume(rid); results.append(dict(name='lifecycle',actual=r['status'],attempts=r['attempts'],repair_in_feedback=feedback[1]['review']['decision']))
replies.append(PASS)
f=Factory(ROOT/'recovery',lambda *a:{},sandbox.verify,reviewer=reviewer); rid=f.create(task); original=f._finish; f._finish=lambda *a: (_ for _ in ()).throw(RuntimeError('crash after verification'))
try:f.resume(rid)
except RuntimeError:pass
try:Factory(f.state,lambda *a:{},sandbox.verify).resume(rid)
except ValueError as e: results.append(dict(name='required-review-recovery',actual='rejected',error=str(e)))
f._finish=original; results.append(dict(name='review-recovery',actual=f.resume(rid)['status'],attempts=f.status(rid)['attempts']))
results.append(dict(name='fresh-context-readonly',actual=all(len(r['messages'])==2 and 'tools' not in r for r in requests)))
for endpoint in ['https://example.org','http://192.168.1.5:8000']:
 try:ModelWorker({'endpoint':endpoint,'model':'x'},sandbox)
 except ValueError:results.append(dict(name='local-only',endpoint=endpoint,actual='rejected'))
(ROOT/'results.json').write_text(json.dumps(results,indent=2)); (ROOT/'http-requests.json').write_text(json.dumps(requests,indent=2)); print(json.dumps(results,indent=2)); server.shutdown()
