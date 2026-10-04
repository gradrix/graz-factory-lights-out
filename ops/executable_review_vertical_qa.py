"""Synthetic no-inference vertical control; only execute after coordinator gate."""
import argparse,json,os,pathlib,socket,time
from unittest.mock import patch
import executable_review_prototype as p

def deny(*a,**kw):raise AssertionError('Controller socket use forbidden in synthetic control')
class FakeTransport:
 def __init__(self):self.calls=0;self.feedback=None
 def request(self,path,body,**kwargs):
  self.calls+=1
  if self.calls==1:
   command="python - <<'PYCODE'\nimport pathlib,sys,json,os\np=pathlib.Path('/candidate/main.py')\ntry:p.write_text('forbidden')\nexcept OSError:blocked=True\nelse:blocked=False\nassert blocked and not pathlib.Path('/workspace').exists() and os.getuid()!=0\nprint(json.dumps({'python':sys.version,'write_blocked':blocked,'cwd':os.getcwd(),'uid':os.getuid()}))\nPYCODE"
   message={'role':'assistant','content':None,'tool_calls':[{'id':'actual','type':'function','function':{'name':'run','arguments':json.dumps({'command':command})}}]};finish='tool_calls'
  else:
   self.feedback=json.loads(body['messages'][-1]['content']);assert self.feedback['exit_code']==0 and '"write_blocked": true' in self.feedback['output']
   message={'role':'assistant','content':json.dumps({'decision':'pass','findings':[],'question':''})};finish='stop'
  return {'choices':[{'message':message,'finish_reason':finish}]}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--bindings',required=True);parser.add_argument('--output',required=True);args=parser.parse_args();root=pathlib.Path(args.output).resolve();root.mkdir();fixtures=pathlib.Path(__file__).resolve().parents[1]/'evaluations/executable-review';manifest=fixtures/'manifest.json';before=p.verify_manifest(manifest,p.digest(manifest.read_bytes()));fake=FakeTransport();original=p.ReviewClient
 class Client(original):
  def __init__(self,config,ledger):super().__init__(config,ledger,transport=fake)
 p.save(root/'config.json',{'endpoint':'http://127.0.0.1:18000','model':'flash-next-coder','reasoning':'medium'});p.CaseLedger.create(root,time.monotonic()+120)
 p.save(root/'spec.json',{'manifest':str(manifest),'manifest_sha256':p.digest(manifest.read_bytes()),'index':1,'bindings':str(pathlib.Path(args.bindings).resolve()),'config':str(root/'config.json')})
 with patch.object(p,'ReviewClient',Client),patch.object(socket.socket,'connect',deny),patch.object(socket,'create_connection',deny):result=p.case_work(root/'spec.json')
 cleanup=p.cleanup_case(root,time.monotonic()+30);assert result['status']=='accepted'and result['attested_commands']==1 and fake.calls==2
 assert p.verify_manifest(manifest,p.digest(manifest.read_bytes()))==before
 p.save(root/'qa-result.json',{'synthetic_only':True,'result':result,'cleanup':cleanup,'transport_calls':fake.calls,'feedback':fake.feedback,'driver_sha256':p.digest(pathlib.Path(__file__).read_bytes()),'mechanism_sha256':p.digest(pathlib.Path(p.__file__).read_bytes()),'manifest_sha256':p.digest(manifest.read_bytes())});print(json.dumps(result))
if __name__=='__main__':main()
