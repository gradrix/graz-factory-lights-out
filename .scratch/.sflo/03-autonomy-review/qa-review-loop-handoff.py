import copy,json,pathlib,tempfile
from qa_pinned import activate
activate('4346ba5289f24f228f83f6f45646f32e41cd48c1')
from gflo.worker import ModelWorker
class Sandbox:
 def cleanup(self,workspace):pass
previous={'passed':False,'review':{'decision':'repair','findings':[{'severity':'major','path':'domain.py','line':1,'evidence':'Quoted token="ALPHA BETA" must stay literal in model evidence','repair':'Correct equality handling'}],'question':''},'checks':[{'exit_code':0,'output':'PASS'}]}
original=copy.deepcopy(previous);requests=[]
with tempfile.TemporaryDirectory() as tmp:
 workspace=pathlib.Path(tmp)/'workspace';workspace.mkdir();worker=ModelWorker({'endpoint':'http://127.0.0.1:1','model':'mock','reasoning':'medium'},Sandbox())
 def response(path,body,timeout):requests.append(copy.deepcopy(body));return {'choices':[{'message':{'role':'assistant','content':'Done'},'finish_reason':'stop'}]}
 worker.request=response;worker(workspace,{'objective':'Repair retained candidate','checks':[['python','check.py']],'max_turns':1},previous,2)
 sent=requests[0];message=next(x['content'] for x in sent['messages'] if x['content'].startswith('Previous attempt evidence'));assert json.loads(message.split('\n',1)[1])==original;assert previous==original
 assert sent['thinking_budget_tokens']==1024 and sent['max_tokens']==4096 and sent['reasoning_effort']=='medium'
 lines=[json.loads(x) for x in (workspace.parent/'attempts/2/trajectory.jsonl').read_text().splitlines()];assert lines;assert 'ALPHA BETA' in json.dumps(lines)  # Known escaped-inner-JSON privacy gap.
print('PASS: current medium coder receives complete original previous-review verdict; trace parses without changing model evidence; reproduced escaped-inner-JSON privacy gap; no network/model calls.')
