"""Build small deterministic USTAR fixtures; never extract any archive."""
import argparse,hashlib,json,pathlib
DEFAULT=pathlib.Path(__file__).resolve().parents[1]
BLOCK=512

def header(name,kind='0',size=0,link='',mode=0o644):
 b=bytearray(BLOCK)
 def text(offset,length,value):
  raw=value.encode('utf-8');assert len(raw)<=length;b[offset:offset+len(raw)]=raw
 def octal(offset,length,value):text(offset,length,format(value,'0'+str(length-1)+'o')+'\0')
 text(0,100,name);octal(100,8,mode);octal(108,8,123);octal(116,8,456);octal(124,12,size);octal(136,12,0)
 b[148:156]=b'        ';text(156,1,kind);text(157,100,link);text(257,6,'ustar\0');text(263,2,'00');text(265,32,'untrusted');text(297,32,'untrusted')
 b[148:156]=format(sum(b),'06o').encode()+b'\0 '
 return bytes(b)

def entry(name,body=b'',kind='0',link='',mode=None,declared=None):
 if mode is None:mode=0o755 if kind=='5' else 0o644
 size=len(body) if declared is None else declared
 return dict(name=name,type=kind,size=size,link=link,mode=oct(mode),body=body)

def archive(entries,trailer=True):
 out=b''
 for e in entries:
  body=e['body'];out+=header(e['name'],e['type'],e['size'],e['link'],int(e['mode'],8))+body+b'\0'*((-len(body))%BLOCK)
 return out+(b'\0'*1024 if trailer else b'')

def pax_record(key,value):
 raw=f'{key}={value}\n';n=len(raw)+2
 while True:
  record=f'{n} {raw}'.encode()
  if len(record)==n:return record
  n=len(record)

DEFAULT_BOUNDS={'transport_bytes':32768,'entries':8,'expanded_bytes':4096,'path_bytes':100}
CASES=[]
def add(id,entries,result,reason,consequence,bounds=None,raw=None,notes=None):
 data=archive(entries) if raw is None else raw
 CASES.append(dict(id=id,entries=entries,data=data,expected_result=result,reason=reason,consequence=consequence,bounds={**DEFAULT_BOUNDS,**(bounds or {})},notes=notes or ''))

valid=[entry('package/',kind='5'),entry('package/__init__.py',b'VERSION = "1.0"\n'),entry('package/data.json',b'{"ready":true,"count":2}\n'),entry('package/tool.py',b'print("tool")\n',mode=0o755)]
add('00-valid-package',valid,'accept','ordinary regular files and directory','Complete validated package can be staged and published after all remaining recipe/smoke checks.')
add('01-duplicate-name',[entry('package/x',b'first'),entry('package/x',b'second')],'reject','duplicate path','No last-entry-wins overwrite; no published receipt or artifact from the attempt.')
add('02-normalized-dot-duplicate',[entry('package/x',b'first'),entry('./package/x',b'second')],'reject','duplicate after POSIX path normalization','Canonical path identity must prevent alias overwrite.')
add('03-normalized-slash-duplicate',[entry('package/x',b'first'),entry('package//x',b'second')],'reject','duplicate after repeated slash normalization','Alternate separator spelling cannot bypass duplicate protection.')
add('04-file-ancestor-first',[entry('package',b'file'),entry('package/child',b'child')],'reject','regular file is ancestor of another path','Reject complete tree before writing; no order-dependent partial extraction.')
add('05-file-ancestor-last',[entry('package/child',b'child'),entry('package',b'file')],'reject','regular file conflicts with already named descendant','Reverse entry order must not bypass prefix-conflict validation.')
add('06-traversal-parent',[entry('../outside',b'escape')],'reject','parent traversal','No artifact writes outside controller-private staging.')
add('07-traversal-nested',[entry('package/../../outside',b'escape')],'reject','nested parent traversal','Normalization cannot conceal an escaping path.')
add('08-absolute',[entry('/outside',b'escape')],'reject','absolute archive path','Archive names cannot select host destinations.')
add('09-symlink',[entry('package/link',kind='2',link='../../outside')],'reject','symbolic link','No link-following writes or runtime dependency escape.')
add('10-hardlink',[entry('package/base',b'content'),entry('package/alias',kind='1',link='package/base')],'reject','hard link','Only regular files/directories are allowed in this bounded profile.')
add('11-arbitrary-bin-symlink',[entry('unrelated/.bin/tool',kind='2',link='../../../outside')],'reject','arbitrary .bin link is not an approved npm omission','Never skip every path containing .bin; only a separately defined precise npm layout may be omitted.')
add('12-character-device',[entry('package/device',kind='3')],'reject','character device entry','Never materialize device nodes.')
add('13-block-device',[entry('package/device',kind='4')],'reject','block device entry','Never materialize device nodes.')
add('14-fifo',[entry('package/pipe',kind='6')],'reject','FIFO entry','Never create filesystem IPC endpoints from package bytes.')
add('15-gnu-sparse-type',[entry('package/sparse',kind='S')],'reject','GNU sparse type encoding','Reject sparse representations before allocation or materialization.',notes='Synthetic old-GNU sparse discriminator; no enormous backing body is present.')
pax=pax_record('GNU.sparse.map','0,1,134217727,1')+pax_record('GNU.sparse.size','134217728')
add('16-pax-sparse',[entry('PaxHeaders/sparse',pax,kind='x'),entry('package/sparse',b'AB')],'reject','PAX GNU sparse metadata','Reject sparse/unsupported extensions; tiny encoded payload must not trigger large expansion.')
add('17-pax-path-override',[entry('PaxHeaders/name',pax_record('path','../outside'),kind='x'),entry('safe-name',b'escape')],'reject','unsupported PAX path override with traversal','Validation must not inspect only the harmless USTAR name while extraction honors an override.')
add('18-gnu-longname-override',[entry('././@LongLink',b'../outside\0',kind='L'),entry('safe-name',b'escape')],'reject','unsupported GNU longname override','Unsupported name extensions cannot bypass path validation.')
add('19-over-entry-count',[entry(f'package/f{i}',b'') for i in range(9)],'reject','nine entries exceed bound eight','Stop bounded enumeration; discard staging without publication.')
add('20-expanded-total',[entry('package/a',b'a'*2048),entry('package/b',b'b'*2048),entry('package/c',b'c')],'reject','4097 regular-file bytes exceed expanded bound 4096','Aggregate expanded limit must apply, not merely a per-file cap.')
add('21-declared-huge',[entry('package/huge',declared=134217729)],'reject','declared file size exceeds expanded limit before payload arrives','Reject from header without allocating declared size or waiting for its bytes.',raw=header('package/huge',size=134217729),notes='Only one 512-byte header exists. Also incomplete transport; rejection must occur without consuming a huge payload. A short fixture alone cannot prove bounded memory or early-read behavior.')
add('22-transport-overlimit',[entry('package/a',b'a'*2048)],'reject','transport bytes exceed explicit bound 2048','Enforce total incoming bytes including headers/padding/trailer.',bounds={'transport_bytes':2048})
add('23-truncated-header',[],'reject','stream ends after 100 bytes of a 512-byte header','Incomplete transport cannot become a complete receipt.',raw=header('package/x',size=1)[:100])
add('24-truncated-payload',[entry('package/x',b'12345678',declared=32)],'reject','header declares 32 bytes but only 8 payload bytes arrive','Do not accept a partially transferred regular file.',raw=header('package/x',size=32)+b'12345678')
add('25-valid-limit-boundary',[entry('package/data',b'x'*4096)],'accept','expanded output equals bound exactly','Inclusive limits must not reject a valid ordinary package at the configured bound.')
add('26-late-bad-entry',[entry('package/good',b'valid'),entry('../outside',b'bad')],'reject','late traversal after valid entry','Full validation must precede extraction; failure leaves no published partial tree.')

SCENARIOS=[
 {'id':'receipt-good','precondition':'Prepare and smoke-check 00-valid-package through future public seam using an approved fixed recipe. Save returned opaque receipt ID and evidence hashes.','operations':['inspect and verify the returned receipt ID','repeat two fresh offline executions using the same frozen binding'],'expected':['same immutable image/dependency binding and actual runtime facts','successful independent recipe smoke checks','no fetch or model call during inspect/verification/execution']},
 {'id':'tamper-file-bytes','precondition':'Start from a separately prepared valid receipt/tree.','operations':['using trusted test control, append one byte to package/data.json after publication','inspect or execute through the public receipt-ID seam'],'expected':['integrity failure before any generated command executes','prior artifact is not silently rehashed or repaired']},
 {'id':'tamper-path-membership','precondition':'Start from independent valid receipt copies.','operations':['in one copy remove package/data.json','in another add an otherwise harmless extra regular file','inspect each receipt'],'expected':['both trees fail integrity verification','tree digest covers path membership as well as existing-file bytes']},
 {'id':'tamper-execution-mode','precondition':'Prepare a valid tree whose controller-selected meaningful execution mode is recorded.','operations':['toggle an execution bit on a regular file without changing its bytes','inspect or execute by receipt ID'],'expected':['integrity failure because meaningful execution mode changed']},
 {'id':'tamper-symlink-replacement','precondition':'Use disposable paths only; do not execute this plan as part of corpus construction.','operations':['replace one regular dependency file with a symlink to another test-owned file','inspect receipt'],'expected':['reject link and do not use target contents to satisfy the original file digest']},
 {'id':'tamper-receipt-binding','precondition':'Start each variant with independently valid published receipt and tree.','operations':['alter the bound base image identity without changing tree bytes','separately alter normalized request/lock identity','separately alter recorded tree binding','inspect or resolve each variant'],'expected':['receipt integrity or binding failure','no substitution of current configured image or unverified tree']},
 {'id':'untrusted-receipt-path','precondition':'Use future documented receipt-ID seam.','operations':['supply ../outside as the receipt ID','supply an absolute path as the receipt ID','supply a forged receipt containing an external mount path if receipt import exists'],'expected':['reject path-like IDs or unsupported receipt input','all mount paths remain controller-derived beneath owned artifact root']},
 {'id':'failed-validation-preserves-good','precondition':'Publish valid baseline receipt G; record G receipt/tree evidence.','operations':['prepare each rejecting archive as a new attempt in the same private store','inspect G after every failure','attempt to resolve any reported failed attempt ID'],'expected':['G remains usable with unchanged identity','failed attempt never becomes runnable','private staging is removed after cleanup succeeds','no outside-file or preexisting-destination write']},
 {'id':'publication-failure','precondition':'Publish G, then prepare valid candidate H in fresh staging on same filesystem.','operations':['use a bounded test-owned fault at atomic publication before successful completion','inspect G and try resolving H'],'expected':['G remains unchanged and usable','H is absent or explicitly failed, never half-published','incomplete receipt/tree cannot pass inspection']},
 {'id':'cancel-before-publication','precondition':'Prepare valid H through completed smoke check but before publication.','operations':['revoke eligibility by cancellation or supersession','allow delayed producer/completion callback to arrive','inspect store and G'],'expected':['H cannot publish after cancellation even when smoke passed','G remains unchanged','executor removal and staging cleanup evidence are required before reuse']},
 {'id':'cancel-mid-transport','precondition':'Start bounded streaming receipt of a valid package using a disposable test producer.','operations':['pause after header and cancel owner','separately exercise owner death','attempt delayed completion'],'expected':['publication eligibility is revoked before cleanup','producer/executor removal is confirmed','staging is discarded and no late receipt appears']},
 {'id':'cleanup-failure-blocks-reuse','precondition':'Have a valid G and an in-flight failed preparation.','operations':['simulate cleanup/daemon unavailability through a future narrow fault seam','attempt reuse of the failed attempt'],'expected':['explicit cleanup failure and blocked failed-attempt reuse until reconciliation','no false claim of removed executors','G identity retained']},
 {'id':'preexisting-destination-symlink','precondition':'All sentinels and links live in a disposable test-owned directory.','operations':['place a symlink in an existing unrelated destination that points to a test sentinel','prepare 00-valid-package through public seam'],'expected':['implementation uses fresh private staging or refuses unsafe reuse','sentinel bytes remain unchanged','no extraction path follows preexisting links']}
]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,default=DEFAULT);args=ap.parse_args();root=args.out; (root/'archives').mkdir(parents=True,exist_ok=True)
 rows=[]
 for c in CASES:
  data=c['data'];name='archives/'+c['id']+'.tar';(root/name).write_bytes(data)
  rows.append({k:v for k,v in c.items() if k not in ['entries','data']}|{'archive':name,'sha256':hashlib.sha256(data).hexdigest(),'transport_size':len(data),'raw_entries':[dict((k,v) for k,v in e.items() if k!='body')|{'stored_body_size':len(e['body']),'stored_body_sha256':hashlib.sha256(e['body']).hexdigest()} for e in c['entries']]})
 (root/'cases.json').write_text(json.dumps(rows,indent=2)+'\n')
 (root/'receipt-publication-scenarios.json').write_text(json.dumps({'status':'acceptance-plan inputs, not executed implementation tests','scenarios':SCENARIOS},indent=2)+'\n')
 records=[]
 for e in valid:
  records.append({'path':e['name'].rstrip('/'),'kind':'directory' if e['type']=='5' else 'regular','size':len(e['body']),'sha256':None if e['type']=='5' else hashlib.sha256(e['body']).hexdigest(),'archive_mode':e['mode']})
 (root/'valid-tree-records.json').write_text(json.dumps({'description':'Independent content inventory; not a mandated tree-digest serialization. Controller selects final safe modes and binds meaningful execution modes. Archive UID123/GID456/untrusted names must not be preserved as authority.','entries':records},indent=2)+'\n')
if __name__=='__main__':main()
