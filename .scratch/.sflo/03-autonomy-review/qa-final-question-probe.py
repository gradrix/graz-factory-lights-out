import json,subprocess,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from qa_pinned import activate,evidence
activate('04c7ef6111e6ed0aef07842528b3137f6a39e7f8')
from gflo.runner import Factory
from gflo.worker import ModelWorker
from gflo.review import Reviewer
from gflo.sandbox import Sandbox
ROOT=evidence('qa-final-question-evidence'); ROOT.mkdir(exist_ok=True)
repo=ROOT/'repo'; repo.mkdir(); (repo/'app.py').write_text('value = 2\n')
for cmd in [['git','init','-q',str(repo)],['git','-C',str(repo),'add','.'],['git','-C',str(repo),'-c','user.name=QA','-c','user.email=qa@local','commit','-qm','fixture']]:subprocess.run(cmd,check=True)
a=ROOT/'acceptance'; a.mkdir(); (a/'check.py').write_text("from pathlib import Path\nassert Path('/workspace/app.py').read_text() == 'value = 2\\n'\n")
objective='Set value to 2. Inputs are integers. The subscription price is explicitly undecided.'
task=ROOT/'task.json'; task.write_text(json.dumps(dict(repo=str(repo),acceptance=str(a),objective=objective,checks=[['python','-I','/acceptance/check.py']],max_attempts=2,max_turns=5)))
queue=[]; requests=[]
class HTTP(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length'])))); response=queue.pop(0)
  if response==503:self.send_response(503); self.end_headers(); return
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps(response).encode())
server=ThreadingHTTPServer(('127.0.0.1',0),HTTP);threading.Thread(target=server.serve_forever,daemon=True).start()
def content(x):return {'choices':[{'message':{'role':'assistant','content':json.dumps(x)}}]}
def question(q):return {'choices':[{'message':{'role':'assistant','content':None,'tool_calls':[{'id':'q1','type':'function','function':{'name':'question','arguments':json.dumps({'question':q})}}]}}]}
PASS={'decision':'pass','findings':[],'question':''}
NO={'needed':False,'basis':'Set value to 2.','guidance':'Value is already specified as 2.'}
YES={'needed':True,'basis':'The subscription price is explicitly undecided.','guidance':'Ask the person for the price.'}
results=[]
def run(name,replies,expected):
 assert not queue
 queue.extend(replies); start=len(requests)
 sandbox=Sandbox();worker=ModelWorker({'endpoint':f'http://127.0.0.1:{server.server_port}','model':'fake-local'},sandbox)
 f=Factory(ROOT/name,worker,sandbox.verify,cleanup=sandbox.cleanup,reviewer=Reviewer(worker));rid=f.create(task)
 try:r=f.resume(rid);error=''
 except Exception as e:r=f.status(rid);error=type(e).__name__+': '+str(e)
 observed=dict(name=name,expected=expected,actual=r['status'],attempts=r['attempts'],error=error,run=rid,requests=len(requests)-start)
 results.append(observed);assert r['status']==expected,observed
 return f,rid,requests[start:]
f,rid,req=run('proceed',[question('What value should I use?'),content(NO),content('Done'),content(PASS)],'accepted')
assert json.loads(req[2]['messages'][-1]['content'])['question_needed'] is False
assert len(req[1]['messages'])==2 and 'tools' not in req[1]
q='What subscription price should be charged?'
f,rid,req=run('needed',[question(q),content(YES)],'needs_input')
worker=json.loads((f.state/rid/'attempts/1/worker.json').read_text());assert worker['question']==q and worker['question_review']==YES
assert f.resume(rid)['attempts']==1
for name,response in [('malformed',content({})),('unavailable',503),('ungrounded',content(dict(NO,basis='Invented objective phrase'))),('wrong-type',content(dict(NO,needed=0))),('invalid-json',{'choices':[{'message':{'content':'not json'}}]}),('blank-guidance',content(dict(NO,guidance='   '))),('empty-choices',{'choices':[]})]:
 f,rid,req=run(name,[question(q),response],'interrupted');assert len(req)==2
 assert results[-1]['error'].startswith('RuntimeError:'),results[-1]
 assert not (f.state/rid/'attempts/1/verification.json').exists()
repair={'decision':'repair','findings':[{'severity':'major','path':'app.py','line':1,'evidence':'Review requests another check','repair':'Inspect value'}],'question':''}
f,rid,req=run('repair-after-proceed',[question('Which value?'),content(NO),content('Done'),content(repair),content('Rechecked'),content(PASS)],'accepted')
assert f.status(rid)['attempts']==2
assert 'Previous attempt evidence' in req[4]['messages'][-1]['content']
(ROOT/'results.json').write_text(json.dumps(results,indent=2));(ROOT/'requests.json').write_text(json.dumps(requests,indent=2));print(json.dumps(results,indent=2));server.shutdown()
