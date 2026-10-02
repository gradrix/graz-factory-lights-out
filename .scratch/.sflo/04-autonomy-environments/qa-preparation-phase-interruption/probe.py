import hashlib,json,pathlib,sys,tempfile,shutil,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('25f75c3275739cc7cc2a4fc5a4e16580b81511d1')
import gflo.prepare as prep
from gflo.environment import EnvironmentStore
import subprocess
OUT=pathlib.Path(__file__).resolve().parent;ROOT=pathlib.Path(tempfile.mkdtemp(prefix='gflo-phase-qa-'));rows=[]
def save():(OUT/'results.json').write_text(json.dumps({'candidate':'25f75c3275739cc7cc2a4fc5a4e16580b81511d1','root':str(ROOT),'results':rows},indent=2)+'\n')
def inventory(store):return {str(p.relative_to(store.root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob('*') if p.is_file() and not any(s.startswith('.') for s in p.relative_to(store.root).parts)}
real_execute=prep.execute;real_smoke=prep.smoke;original_recipes=prep.RECIPES;original_code=prep.PYTHON_SMOKE;observed=[]
def execute(*args,**kwargs):
 try:return real_execute(*args,**kwargs)
 finally:
  for p in pathlib.Path(args[2]).glob('*.json'):
   value=json.loads(p.read_text())
   if value['name'] not in [v['name'] for v in observed]:observed.append(value)
prep.execute=execute
# Actual online fetch executor; only private helper adds a no-network DNS wait.
recipes=ROOT/'recipes';shutil.copytree(original_recipes,recipes);helper=recipes/'fetch.py';text=helper.read_text();text=text.replace("    records = socket.getaddrinfo", "    import time\n    print('QA_SIMULATED_DNS_WAIT', file=sys.stderr, flush=True)\n    time.sleep(60)\n    records = socket.getaddrinfo",1);helper.write_text(text);prep.RECIPES=recipes
store=EnvironmentStore(ROOT/'fetch');observed.clear();started=time.monotonic()
try:prep.prepare(store,'python-api',timeout=3)
except ValueError as e:error=str(e)
else:raise AssertionError('fetch wait accepted')
assert '124' in error and 'QA_SIMULATED_DNS_WAIT' in error;assert not inventory(store);assert len(observed)==1 and observed[0]['host']['NetworkMode']=='bridge'
for item in observed:assert subprocess.run(['docker','inspect',item['name']],capture_output=True,timeout=10).returncode!=0
rows.append({'phase':'fetch','fault':'simulated blocked DNS in actual fetch container','error':error,'elapsed':time.monotonic()-started,'executors':observed.copy(),'removed':True,'no_receipt':True});save();prep.RECIPES=original_recipes
# Final publication smoke: preserve existing valid receipt, cancel while .prepare staging exists.
store=EnvironmentStore(ROOT/'final-smoke');good=prep.prepare(store,'python-stdlib');before=inventory(store);observed.clear();count=0;armed=None;staging_seen=False

def smoke(*args,**kwargs):
 global count,armed,staging_seen
 count+=1
 if count==2:
  assert any(p.name.startswith('.prepare-') for p in store.root.iterdir());staging_seen=True;armed=time.monotonic()
  prep.PYTHON_SMOKE="import time; print('QA_FINAL_SMOKE_WAIT', flush=True); time.sleep(60)\n"+original_code
 try:return real_smoke(*args,**kwargs)
 finally:prep.PYTHON_SMOKE=original_code
prep.smoke=smoke
try:prep.prepare(store,'python-stdlib',cancelled=lambda:armed is not None and time.monotonic()-armed>2)
except ValueError as e:error=str(e)
else:raise AssertionError('final smoke interruption accepted')
assert count==2 and staging_seen and '130' in error and 'QA_FINAL_SMOKE_WAIT' in error
assert inventory(store)==before and store.resolve(good.id).receipt_hash==good.receipt_hash
assert not list(store.root.glob('.prepare-*')) and not list(store.root.glob('.work-*'))
for item in observed:assert subprocess.run(['docker','inspect',item['name']],capture_output=True,timeout=10).returncode!=0
rows.append({'phase':'final-publication-smoke','fault':'cancellation during second actual smoke executor','error':error,'executors':observed.copy(),'staging_seen':True,'removed':True,'prior_good_unchanged':True});save()
prep.smoke=real_smoke;recovered=prep.prepare(store,'python-stdlib');assert recovered.id==good.id;rows.append({'phase':'recovery','same_prior_good_id':recovered.id,'passed':True});save();print('PASS fetch timeout and final-smoke cancellation/preservation/recovery')
