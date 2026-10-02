"""Serial frozen extension cohort; uses the already qualified two-question harness."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path('/home/gradrix/gflo-stage4-9c01da1')
contracts=root/'research-cohort'
manifest=contracts/'manifest.json'
assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='754374e1644559cf37d405e30735b442e7691200ac183e4a49b0cbdfb9d3e797'
assert hashlib.sha256((root/'qualify-documents.py').read_bytes()).hexdigest()=='efb7e5734c2bd84ec25c55791b850128161932b90cece577cc9941739b1d5890'
out=root/'.gflo/research-cohort';out.mkdir(exist_ok=False)
results=[]
for name,digest in json.loads(manifest.read_text())['contracts'].items():
 assert hashlib.sha256((contracts/name).read_bytes()).hexdigest()==digest
 target=out/Path(name).stem
 args=[sys.executable,str(root/'qualify-documents.py'),'--repo',str(root),'--candidate',str(root/'.scratch/.sflo/05-autonomy-documents/builder-candidate-v2.json'),'--candidate-sha256','9c01da103e9f145bfc426e4a4c3f02780b85a845594a4716d1437d36c413cb3c','--contract',str(contracts/name),'--contract-sha256',digest,'--config','/home/gradrix/gflo-runtime/.gflo/config.json','--serving-container','gflo-model','--expected-serving-id','2cac4229053dac00fdbcadb1952db80f0a9da3fd07b8f40bce1ba8cd3114f6e0','--expected-serving-image','sha256:249ed60fdd67b96db472e16f945af5aaba565b20159d192ba378035b6d136a1c','--output',str(target),'--run']
 result=subprocess.run(args,capture_output=True,text=True)
 (out/(Path(name).stem+'.log')).write_text(result.stdout+result.stderr)
 receipt=json.loads((target/'receipt.json').read_text())
 results.append({'contract':name,'exit':result.returncode,'status':receipt['status'],'questions':receipt['questions'],'elapsed_s':receipt['elapsed_s']})
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results[-1]),flush=True)
