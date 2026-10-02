import ast,copy,hashlib,json,pathlib,runpy,tempfile,unittest.mock as mock
p=pathlib.Path(__file__).with_name('repair-reasoning-probe.py');x=runpy.run_path(str(p));calls=[]
def fake(self,path,body=None,timeout=300):
 calls.append(copy.deepcopy(body));return {'choices':[{'finish_reason':'stop'}],'usage':{'total_tokens':3}}
config={'endpoint':'http://127.0.0.1:1','model':'mock','reasoning':'none'}
body={'tools':[{}],'max_tokens':4096,'temperature':0,'reasoning_effort':'none','chat_template_kwargs':{'enable_thinking':False},'messages':[]}
with mock.patch.object(x['ModelWorker'],'request',fake):
 for thinking in [False,True]:
  records=[];worker=x['ProbeWorker'](config,None,records,thinking=thinking);worker.request('/v1/chat/completions',body,timeout=21);wire=calls[-1];record=records[-1]
  assert wire['reasoning_effort']==('medium' if thinking else 'none')
  assert wire['chat_template_kwargs']=={'enable_thinking':thinking}
  assert wire.get('thinking_budget_tokens')==(1024 if thinking else None)
  assert record['effective_profile']['thinking_budget_tokens']==wire.get('thinking_budget_tokens')
  assert record['request_sha256']==hashlib.sha256(json.dumps(wire).encode()).hexdigest()
  assert record['request_bytes']==len(json.dumps(wire).encode())
  assert record['timeout_seconds']==21 and record['usage']['total_tokens']==3
  assert body['chat_template_kwargs']=={'enable_thinking':False} and 'thinking_budget_tokens' not in body
  other={'max_tokens':4096,'reasoning_effort':'medium','thinking_budget_tokens':1024,'chat_template_kwargs':{'enable_thinking':True}}
  worker.request('/v1/chat/completions',other);assert calls[-1]==other and len(records)==1
with mock.patch.object(x['ModelWorker'],'request',side_effect=RuntimeError('mock')):
 records=[];worker=x['ProbeWorker'](config,None,records,thinking=True)
 try:worker.request('/v1/chat/completions',body)
 except RuntimeError:pass
 assert records[0]['error_type']=='RuntimeError' and 'elapsed_seconds' in records[0]
tree=ast.parse(p.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');loop=next(n for n in ast.walk(main) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='record');nodes=loop.body;start=next(i for i,n in enumerate(nodes) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='verification' for t in n.targets));end=next(i for i,n in enumerate(nodes[start:],start) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='save');code=compile(ast.Module(body=nodes[start:end],type_ignores=[]),'receipt_extract','exec')
with tempfile.TemporaryDirectory() as temp:
 root=pathlib.Path(temp);prior=root/'prior';prior.mkdir();(prior/'review.json').write_text('{"decision":"pass"}');failed=root/'failed';failed.mkdir();scope={'attempt':failed,'record':{},'json':json,'review_path':prior/'review.json'};exec(code,scope);assert scope['record']=={} and scope['review_path']==failed/'review.json'
 (failed/'verification.json').write_text('{"checks":[{"exit_code":0}]}');(failed/'review.json').write_text('{"decision":"repair"}');scope['record']={};exec(code,scope);assert scope['record']=={'acceptance_passed':True,'review_decision':'repair'}
print('PASS: both wire profiles, effective receipts/hash, source-body immutability, non-tool passthrough, exception receipt, missing-verification and current-review controls. No network/GPU.')
print('script_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
