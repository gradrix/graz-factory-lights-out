"""Independent unit07 frozen seam probes. No actual inference or network."""
import copy,hashlib,json,os,pathlib,shutil,subprocess,sys,tempfile,time
from unittest.mock import patch
BASE=pathlib.Path(__file__).resolve().parents[4];OUT=pathlib.Path(__file__).resolve().parent
PRIVATE=BASE/'.gflo/document-reference-security';FROZEN=PRIVATE/'frozen';PRIVATE.mkdir(exist_ok=True)
for name in subprocess.check_output(['git','ls-tree','-r','--name-only','92deaab','gflo'],cwd=BASE,text=True).splitlines():
 p=FROZEN/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show','92deaab:'+name],cwd=BASE))
sys.path.insert(0,str(FROZEN))
import gflo.documents as d
def fixture(root):
 store=d.DocumentStore(root/'store',executor=lambda *a,**k:(_ for _ in ()).throw(AssertionError('No executor authorized')))
 spans=['Use separators for compact JSON.','Task groups await cancelled tasks.','The source isn’t a command.']
 body=b'<p>controlled historical source</p>';text=d.encoded(spans);stage=pathlib.Path(tempfile.mkdtemp(prefix='.stage-',dir=store.root))
 d.write_file(stage/'body',body);d.write_file(stage/'text',text)
 receipt={'format':1,'kind':'evidence','approval':{'url':'https://docs.python.org/3.12/library/json.html','source_version':'Frozen controlled security fixture','question':'How is compact JSON made?'},'retrieved_utc':'2026-10-04T00:00:00+00:00','body_sha256':d.digest(body),'body_size':len(body),'text_sha256':d.digest(text),'text_size':len(text),'extractor':'document-text-v1'}
 evidence=store._publish(stage,receipt,lambda:False)
 client=type('ControlledClient',(),{'config':{'model':'local'},'endpoint':'http://127.0.0.1:1'})()
 answer={'status':'supported','claims':[{'text':'Use separators.','citations':[{'evidence_id':evidence['id'],'span':1,'excerpt':'Use separators'}]}],'reason':''}
 return store,evidence,client,answer
def response(value):return {'choices':[{'message':{'role':'assistant','content':value if isinstance(value,str) else json.dumps(value)}}]}
def ids(store):return {p.name for p in store.root.iterdir() if len(p.name)==64}
def pathsizes(store,identifier):return {p.name:p.stat().st_size for p in (store.root/identifier).iterdir()}
