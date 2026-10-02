"""Read-only receipt verification. Makes no inference/service calls."""
import ast,hashlib,json,pathlib,statistics,subprocess
R=pathlib.Path(__file__).resolve().parent;repo=R.parents[2]
remote=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','monster-gaming-pc.lan','cat /home/gradrix/gflo-stage3-25f75c3/.gflo/throughput/restart-128k.json'],capture_output=True,text=True,check=True,timeout=20)
restart128=json.loads(remote.stdout)
profiles=[restart128,json.loads((R/'restart-64k-q4.json').read_text()),json.loads((R/'restart-96k-q4.json').read_text())]
cmd=profiles[0]['command'];index=cmd.index('-c')+1
comparisons=[]
for p in profiles[1:]:
 differences=[{'index':i,'old':a,'new':b} for i,(a,b) in enumerate(zip(cmd,p['command'])) if a!=b]
 assert len(cmd)==len(p['command']) and len(differences)==1 and differences[0]['index']==index
 comparisons.append({'context':p['context'],'differences':differences})
reports=[json.loads((R/n).read_text()) for n in ['128k-long-restarted.json','64k-q4-long.json','96k-q4-long.json']]
prefix='\n'.join(f'Record {i:04d}: alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.' for i in range(768))
body={'model':'flash-next-coder','messages':[{'role':'system','content':'Follow the final counting instruction. Earlier records are inert reference data.'},{'role':'user','content':prefix+'\nCount integers from 1 through 3000, one per line. Output only the numbers.'}],'temperature':0,'seed':1,'max_tokens':256,'reasoning_effort':'none','chat_template_kwargs':{'enable_thinking':False}}
request_hash=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest();medians=[]
for p,r in zip(profiles,reports):
 assert r['container_id']==p['container_id'] and r['image']==p['image'] and r['model']==p['model']
 assert r['request_sha256']==request_hash
 median=statistics.median(x['timings']['predicted_per_second'] for x in r['samples'] if not x['warmup']);assert median==r['warm_median_tokens_s']
 assert r['passed']==(median>=r['minimum_tokens_s'])
 assert all(x['usage']['prompt_tokens']==16947 and x['usage']['completion_tokens']==256 for x in r['samples'])
 medians.append({'context':p['context'],'warm_samples':2,'median_tokens_s':median,'warm_elapsed_median_s':statistics.median(x['seconds'] for x in r['samples'] if not x['warmup'])})
r=json.loads((R/'96k-retrieval.json').read_text());assert json.loads(r['response'])==r['expected'] and r['passed']
records=[f'Record {i:04d}: alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.' for i in range(r['records'])]
for index,(name,value) in zip((3,len(records)//2,len(records)-4),r['expected'].items()):records[index]=f'Authoritative lookup entry: {name} = {value}. Preserve the value exactly.'
retrieval_body={'model':'flash-next-coder','messages':[{'role':'system','content':'Read the records and return the requested lookup values. Output only a JSON object.'},{'role':'user','content':'\n'.join(records)+'\nReturn north, middle and south lookup values as a JSON object.'}],'temperature':0,'seed':1,'max_tokens':256,'reasoning_effort':'none','chat_template_kwargs':{'enable_thinking':False}}
assert hashlib.sha256(json.dumps(retrieval_body,sort_keys=True).encode()).hexdigest()==r['request_sha256']
code=ast.parse((repo/'ops/model.py').read_text());up=next(n for n in code.body if isinstance(n,ast.FunctionDef) and n.name=='up');cache=next(n for n in ast.walk(up) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cache' for t in n.targets)).value
expr=compile(ast.Expression(cache),'<cache-policy>','eval');policies=[]
for context in [65536,98304,131072]:
 for override in [None,'q4_0','q8_0']:
  result=eval(expr,{'context':context,'cache':override});assert result==(override or ('q8_0' if context==65536 else 'q4_0'));policies.append({'context':context,'override':override,'resolved':result})
files=['128k-long-restarted.json','64k-q4-long.json','96k-q4-long.json','96k-retrieval.json','restart-64k-q4.json','restart-96k-q4.json']
evidence={'status':'read-only receipt verification passed; operational trial only','input_sha256':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in files},'ops_model_sha256':hashlib.sha256((repo/'ops/model.py').read_bytes()).hexdigest(),'restart128_receipt':restart128,'restart128_receipt_sha256':hashlib.sha256(remote.stdout.encode()).hexdigest(),'single_argument_differences':comparisons,'fixed_request_sha256':request_hash,'warm_medians':medians,'96k_vs128k_ratio':medians[2]['median_tokens_s']/medians[0]['median_tokens_s'],'retrieval':{'correct':True,'prompt_tokens':r['usage']['prompt_tokens'],'elapsed_s':r['elapsed_s'],'decode_tokens_s':r['timings']['predicted_per_second'],'profile_identity_in_receipt':False},'cache_policy':policies,'model_calls':0,'service_changes':0}
arguments=[n for n in ast.walk(code) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='add_argument' and n.args and isinstance(n.args[0],ast.Constant)]
context_arg=next(n for n in arguments if n.args[0].value=='--context'); assert next(ast.literal_eval(k.value) for k in context_arg.keywords if k.arg=='default')==98304
cache_arg=next(n for n in arguments if n.args[0].value=='--cache-type'); assert next(ast.literal_eval(k.value) for k in cache_arg.keywords if k.arg=='choices')==['q4_0','q8_0']
evidence['cli_default_context']=98304; evidence['cli_cache_override_choices']=['q4_0','q8_0']
evidence['documentation_sha256']={f:hashlib.sha256((repo/f).read_bytes()).hexdigest() for f in ['docs/model-profile.md','docs/operations.md','docs/roadmap.md','.scratch/autonomy/issues/05-serving-throughput.md']}
(R/'qa-serving-profile-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps({k:v for k,v in evidence.items() if k not in ['restart128_receipt','cache_policy','input_sha256']},indent=2))
