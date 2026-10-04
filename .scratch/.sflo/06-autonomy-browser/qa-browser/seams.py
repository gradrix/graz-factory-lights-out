import pathlib,sys,json,shutil,tempfile,subprocess,io,contextlib,time,hashlib
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path.cwd()))
from gflo.browser import BrowserStore
from gflo.browser_pair import run
from gflo.__main__ import main
out=pathlib.Path(__file__).resolve().parent;results=json.loads(pathlib.Path('.gflo/browser-independent-v2/results.json').read_text());good=results['rows'][0]['id'];support=results['support_id'];source=pathlib.Path('.gflo/browser-independent-v2/store').resolve();root=pathlib.Path(tempfile.mkdtemp(prefix='gflo-browser-seams-'));store=BrowserStore(root/'store')
for name in [support,good]:shutil.copytree(source/name,store.root/name)
def hashes(p):return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
before=hashes(store.root/good)
with patch('gflo.__main__.ModelWorker',side_effect=AssertionError('inference')),patch('gflo.browser.subprocess.run',side_effect=AssertionError('executor started')),contextlib.redirect_stdout(io.StringIO()) as s:assert main(['--config','/nonexistent','browser','--store',str(store.root),'inspect',good])==0
assert json.loads(s.getvalue())==store.inspect(good);assert hashes(store.root/good)==before
checks=root/'checks';checks.mkdir();(checks/'journey.cjs').write_text("module.exports=async()=>{require('fs').writeFileSync('/tmp/qa-journey-entered','1');await new Promise(()=>{});};\n")
observed=[]
def executor(spec,stream,**kw):
 def cancelled():
  p=subprocess.run(['docker','exec',spec['browser_name'],'test','-f','/tmp/qa-journey-entered'],capture_output=True,timeout=5)
  if p.returncode==0:observed.append(spec['browser_name']);return True
  return False
 return run(spec,stream,cancelled=cancelled)
store=BrowserStore(store.root,executor=executor);case=pathlib.Path('evaluations/local-browser/journeys/create-reload').resolve();t=time.monotonic();cancelled=store.check({'app':str(pathlib.Path('evaluations/local-browser/app').resolve()),'checks':str(checks),'seed':str(case/'seed.json'),'case':'qa-cancel-inside-journey','support':support});receipt=cancelled['receipt'];assert observed and receipt['outcome']['status']=='failed';assert receipt['executor']['facts']['cleanup']['confirmed'];assert hashes(store.root/good)==before
remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.browser='+store.label],text=True,timeout=10).split();assert not remaining;assert store.inspect(good)['id']==good
(out/'seams-results.json').write_text(json.dumps({'root':str(root),'offline_cli_inspect':True,'prior_good_preserved':True,'cancel_elapsed_s':time.monotonic()-t,'cancelled_result':cancelled,'remaining':remaining},indent=2)+'\n');print('PASS offline CLI inspect and actual in-journey cancellation/prior good')
