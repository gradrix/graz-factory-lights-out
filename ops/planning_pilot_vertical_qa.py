"""Synthetic reference injection through real arm_work, Factory and offline Docker.
No model: controller sockets denied; only a networkless transport is installed.
Private proof only. Never use this script to run an experimental arm.
"""
import argparse,base64,hashlib,json,pathlib,socket,time
from unittest.mock import patch
import planning_pilot_prototype as p

def deny(*a,**k):raise AssertionError('Controller network forbidden in synthetic QA')
def response(content=None,call=None):
 message={'role':'assistant','content':content}
 if call:message['tool_calls']=[{'id':'synthetic','type':'function','function':call}]
 return {'choices':[{'message':message,'finish_reason':'tool_calls'if call else 'stop'}]}
class Synthetic:
 def __init__(self,case,reference):self.case=case;self.reference=reference
 def request(self,path,body,**kw):
  assert path=='/v1/chat/completions'
  system=body['messages'][0]['content']
  if body.get('tools'):
   tools=[m for m in body['messages']if m['role']=='tool']
   if not tools:return response(call={'name':'question','arguments':json.dumps({'question':'Are the explicitly stated requirements authoritative?'})})
   if len(tools)==1:
    files={str(f.relative_to(self.reference)):base64.b64encode(f.read_bytes()).decode()for f in self.reference.rglob('*')if f.is_file()}
    code='import pathlib,base64,json; files=json.loads('+repr(json.dumps(files))+'); [(pathlib.Path(n).parent.mkdir(parents=True,exist_ok=True),pathlib.Path(n).write_bytes(base64.b64decode(v))) for n,v in files.items()]'
    return response(call={'name':'run','arguments':json.dumps({'command':"python - <<'SYNTHETIC_QA'\n"+code+"\nSYNTHETIC_QA"})})
   return response('Synthetic reference installed; no model inference.')
  if system.startswith('Propose exactly'):
   ids=[r['id']for r in self.case['requirements']]
   result={'tasks':[{'id':'task1','objective':'Implement frozen milestone','requirement_ids':self.case['milestone_requirement_ids'],'depends_on':[]},{'id':'task2','objective':'Complete original requirements','requirement_ids':ids,'depends_on':['task1']}]}
  elif system.startswith('Independently assess'):result={'decision':'pass','reason':'Synthetic control accepts valid fixed plan.'}
  elif system.startswith('You assess whether'):
   payload=json.loads(body['messages'][1]['content']);result={'needed':False,'basis':payload['objective'][:60],'guidance':'Follow the explicit requirements.'}
  else:result={'decision':'pass','findings':[],'question':''}
  return response(json.dumps(result))
def main():
 a=argparse.ArgumentParser();a.add_argument('--bindings',required=True);a.add_argument('--output',required=True);args=a.parse_args()
 root=pathlib.Path(args.output).resolve();root.mkdir();fixtures=pathlib.Path(__file__).resolve().parents[1]/'evaluations/planning-pilot';manifest=json.loads((fixtures/'manifest.json').read_text());rows=[]
 original=p.BudgetWorker
 for index,case in enumerate(manifest['cases']):
  arm=root/case['id'];arm.mkdir();p.save(arm/'budget.json',{'limit':48,'calls':[],'deadline':time.monotonic()+300})
  p.save(arm/'config.json',{'endpoint':'http://127.0.0.1:18000','model':'flash-next-coder'})
  spec={'manifest':str(fixtures/'manifest.json'),'manifest_sha256':p.digest((fixtures/'manifest.json').read_bytes()),'case_index':index,'bindings':str(pathlib.Path(args.bindings).resolve()),'config':str(arm/'config.json'),'method':'decomposed'};p.save(arm/'spec.json',spec)
  fake=Synthetic(case,fixtures/'private/references'/case['id'])
  class Client(original):
   def __init__(self,config,sandbox,budget):
    super().__init__({**config,'endpoint':'http://127.0.0.1:1'},sandbox,budget,transport=fake)
  started=time.monotonic()
  with patch.object(p,'BudgetWorker',Client),patch.object(socket.socket,'connect',deny),patch.object(socket,'create_connection',deny):result=p.arm_work(arm/'spec.json')
  cleanup=p.cleanup_owned(arm,time.monotonic()+60);integrity=p.final_integrity(arm,result);ledger=json.loads((arm/'budget.json').read_text());row={'case':case['id'],'result':result,'integrity':integrity,'cleanup':cleanup,'calls':len(ledger['calls']),'roles':sorted({c['role']for c in ledger['calls']}),'elapsed_s':time.monotonic()-started};rows.append(row);p.save(root/'results.json',rows)
  assert result['status']=='accepted'and integrity,row
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
