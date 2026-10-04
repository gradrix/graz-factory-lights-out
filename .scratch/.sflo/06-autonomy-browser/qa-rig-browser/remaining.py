"""Frozen bounded target probe: controlled tests plus actual public startup cancellation."""
import hashlib,json,os,pathlib,shutil,subprocess,sys,time,unittest
REPO=pathlib.Path('/home/gradrix/gflo-browser-596ecb6');os.chdir(REPO);sys.path.insert(0,str(REPO));sys.path.insert(0,str(REPO/'tests'));os.environ['PYTHONPATH']=str(REPO)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=REPO/'.scratch/.sflo/06-autonomy-browser/builder-candidate-v5.json'
def frozen():
 assert sha(manifest)=='ee60bbe4012e03acbcd5a9cd403a63f62290dd253c97a7f7979ead062ee53ea4'
 for n,h in json.loads(manifest.read_text())['files'].items():assert sha(REPO/n)==h,n
frozen();out=REPO/'.gflo/rig-qualification-v5/remaining';assert not out.exists();out.mkdir(mode=0o700)
names=['test_browser.BrowserArtifactTests','test_browser.BrowserStoreTests.test_uncertain_cleanup_never_publishes_and_fences_next_check','test_browser.BrowserStoreTests.test_uncertain_create_requires_explicit_ack_and_preserves_failure','test_browser.BrowserStoreTests.test_cancellation_during_final_sync_cannot_publish_pass']
with (out/'controlled.log').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
summary={'controlled':{'names':names,'count':result.testsRun,'passed':result.wasSuccessful(),'label':'controlled byte streams and executor/commit/daemon doubles; not actual daemon outage'}};(out/'results.json').write_text(json.dumps(summary,indent=2));assert result.wasSuccessful()
from gflo.browser import BrowserStore
from gflo.browser_pair import run
root=out/'startup';root.mkdir();(root/'app').mkdir();(root/'checks').mkdir();(root/'app/server.cjs').write_text("require('http').createServer((q,r)=>{}).listen(3210,'127.0.0.1')");(root/'checks/journey.cjs').write_text('module.exports=async()=>{}');(root/'seed.json').write_text('{}')
source=REPO/'.gflo/rig-qualification-v5/five-flows/store';support='df4755523d7682b461c222f22f99453346eccef769f6bbc096ac77772a8ffd20';prior='c7b4f99897292badc5c29337e17fec7b5995fad1cd1cd789803abf704b5b77f8';observed=[];spec_saved={};pair_outcomes=[]
def executor(spec,stream,**kw):
 spec_saved.update(spec);value=run(spec,stream,**kw);pair_outcomes.append(value);return value
def cancel():
 if observed:return True
 if not spec_saved:return False
 proc=subprocess.run(['docker','inspect','--format','{{.State.Running}}',spec_saved['app_name']],capture_output=True,text=True,timeout=5)
 if proc.returncode==0 and proc.stdout.strip()=='true':observed.append({'name':spec_saved['app_name'],'running':True,'at':time.monotonic()});return True
 return False
store=BrowserStore(root/'store',executor=executor)
for identifier in [support,prior]:shutil.copytree(source/identifier,store.root/identifier);store.inspect(identifier)
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
before=hashes(store.root/prior);source_before=hashes(source/prior);started=time.monotonic();error=None
try:store.check({'app':str(root/'app'),'checks':str(root/'checks'),'seed':str(root/'seed.json'),'case':'public-startup-cancel','support':support},cancelled=cancel)
except ValueError as e:error=str(e)
remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.browser='+store.label],text=True,timeout=10).split();new_receipts=[p.name for p in store.root.iterdir() if p.is_dir() and (p/'receipt.json').exists() and p.name not in [support,prior]]
summary['startup']={'label':'actual pair, public Store callback after observed running readiness-stalled app','observed':observed,'error':error,'elapsed_s':time.monotonic()-started,'remaining':remaining,'new_receipts':new_receipts,'prior_unchanged':hashes(store.root/prior)==before,'source_prior_unchanged':hashes(source/prior)==source_before,'pair':pair_outcomes};(out/'results.json').write_text(json.dumps(summary,indent=2))
assert observed and error and 'cancelled' in error and not remaining and not new_receipts and summary['startup']['prior_unchanged'] and summary['startup']['source_prior_unchanged'];assert len(pair_outcomes)==1 and pair_outcomes[0]['reason']=='cancelled' and pair_outcomes[0]['facts']['cleanup']['confirmed'];store.inspect(prior);frozen();summary['frozen_hashes_after_match']=True;(out/'results.json').write_text(json.dumps(summary,indent=2));print('PASS four controlled seams and actual public startup cancellation')
