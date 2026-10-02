"""Approved-source fetch and offline bounded extraction experiment. No model calls."""
import hashlib,io,json,os,pathlib,subprocess,sys,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=pathlib.Path(__file__).resolve().parent;WORK=ROOT/'.gflo/document-event-prototype';SNAP=WORK/'accepted';COMMIT='2049361'
WORK.mkdir(parents=True,exist_ok=True)
RUN_OUT=OUT if not (OUT/'results.json').exists() else OUT/('rerun-'+str(time.time_ns()))
RUN_OUT.mkdir(parents=True,exist_ok=True)
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',COMMIT,'gflo'],cwd=ROOT,text=True).splitlines():
 target=SNAP/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(subprocess.check_output(['git','show',COMMIT+':'+name],cwd=ROOT))
sys.path.insert(0,str(SNAP))
from gflo.documents import DocumentStore
from gflo.recipes.document import unpack
from gflo.guard import run
from gflo.sandbox import DEFAULT_IMAGE
APP={'url':'https://docs.python.org/3.12/library/asyncio-task.html','source_version':'Python3.12 historical documentation snapshot; floating series URL','question':'Measure extraction event count only; no inference.'}
source=SNAP/'gflo/recipes/document_extract.py';before=hashlib.sha256((ROOT/'gflo/recipes/document_extract.py').read_bytes()).hexdigest();assert before==hashlib.sha256(source.read_bytes()).hexdigest()
bodyfile=WORK/'asyncio-body.html'
if not bodyfile.exists():
 store=DocumentStore(WORK/'fetch-store');capture=WORK/'fetch-work';capture.mkdir(exist_ok=True)
 started=time.monotonic();framed,facts=store._execute('fetch',capture,APP,cancelled=lambda:False);metadata,body=unpack(framed,APP);bodyfile.write_bytes(body)
 ((OUT if not (OUT/'acquisition.json').exists() else RUN_OUT)/'acquisition.json').write_text(json.dumps({'approved':APP,'http':metadata,'body_sha256':hashlib.sha256(body).hexdigest(),'elapsed_s':time.monotonic()-started,'executor':facts,'source_commit':COMMIT},indent=2)+'\n')
else:
 previous=json.loads((OUT/'acquisition.json').read_text());assert hashlib.sha256(bodyfile.read_bytes()).hexdigest()==previous['body_sha256']
cases=[]
for limit in [10000,40000]:
 for repeat in range(3):cases.append((f'asyncio-{limit}-repeat{repeat+1}',bodyfile,limit,'passed' if limit==40000 else 'rejected'))
 for n in [limit,limit+1]:
  path=WORK/f'events-{n}.html';path.write_bytes(b'<!--x-->'*(n-3)+b'<p>x</p>');cases.append((f'events-{limit}-actual{n}',path,limit,'passed' if n==limit else 'rejected'))
for name,body,want in [('depth64',b'<div>'*64+b'x'+b'</div>'*64,'passed'),('depth65',b'<div>'*65+b'x'+b'</div>'*65,'rejected'),('text131072',b'<p>'+b'x'*131072+b'</p>','passed'),('text131073',b'<p>'+b'x'*131073+b'</p>','rejected'),('blocks2048',b'<p>x</p>'*2048,'passed'),('blocks2049',b'<p>x</p>'*2049,'rejected')]:
 path=WORK/(name+'.html');path.write_bytes(body);cases.append((name,path,40000,want))
rows=[]
for name,body,limit,expected in cases:
 cname='gflo-document-event-'+uuid.uuid4().hex[:16];inspection=WORK/(name+'-inspect.json')
 args=['docker','run','--rm','--pull','never','--name',cname,'--label','gflo.prototype=document-event','--runtime','runc','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user',f'{os.getuid()}:{os.getgid()}','--memory','256m','--memory-swap','256m','--cpus','1','--pids-limit','64','--shm-size','8m','--tmpfs','/tmp:rw,nosuid,nodev,size=16m,mode=1777','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--workdir','/tmp']
 for a,b in [(body,'/body'),(source,'/helpers/document_extract.py'),(OUT/'measure.py','/helpers/measure.py')]:args+=['--mount',f'type=bind,src={a},dst={b},readonly']
 args += [DEFAULT_IMAGE,'python','-B','/helpers/measure.py',str(limit)]
 capture=io.BytesIO();started=time.monotonic();result=run(args,cname,5,output=capture,max_output_bytes=8192,inspect_path=inspection);elapsed=time.monotonic()-started
 assert result['exit_code']==0,(name,result)
 measurement=json.loads(capture.getvalue());assert measurement['status']==expected,(name,measurement)
 absent=subprocess.run(['docker','ps','-aq','--filter','name=^/'+cname+'$'],capture_output=True,text=True,check=True,timeout=10);assert not absent.stdout.strip()
 facts=json.loads(inspection.read_text());facts.pop('name',None)
 for mount in facts['mounts']:mount.pop('Source',None)
 rows.append({'case':name,'expected':expected,'measurement':measurement,'guardian_elapsed_s':elapsed,'guardian':result,'executor':facts,'container_absent':True})
 (RUN_OUT/'results.json').write_text(json.dumps({'accepted_commit':COMMIT,'extractor_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'measurement_helper_sha256':hashlib.sha256((OUT/'measure.py').read_bytes()).hexdigest(),'body_limit':2097152,'text_limit':131072,'depth_limit':64,'block_limit':2048,'work_timeout_s':5,'memory_bytes':268435456,'results':rows},indent=2)+'\n')
 print(name,measurement['status'],'events',measurement['events'],'text',measurement['text_bytes'],'spans',measurement['spans'],'wall',round(measurement['extract_wall_s'],4),'rssKiB',measurement['process_peak_rss_kib'],flush=True)
after=hashlib.sha256((ROOT/'gflo/recipes/document_extract.py').read_bytes()).hexdigest();assert before==after
(RUN_OUT/'source-unchanged.json').write_text(json.dumps({'maintained_extractor_before':before,'maintained_extractor_after':after,'changed_only_in_process_constant':'EVENT_LIMIT:10000→40000'},indent=2)+'\n')
