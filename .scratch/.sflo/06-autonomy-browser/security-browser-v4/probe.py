"""Independent frozen browser-v4 probes; no maintained edits or model calls."""
import hashlib, io, json, os, pathlib, shutil, struct, subprocess, sys, tempfile
from unittest.mock import patch
BASE=pathlib.Path(__file__).resolve().parents[4]
PRIVATE=BASE/'.gflo/browser-security-v4'
FROZEN=PRIVATE/'frozen'
OUT=pathlib.Path(__file__).resolve().parent
def reconstruct():
    for name in subprocess.check_output(['git','ls-tree','-r','--name-only','6852a20','gflo'],cwd=BASE,text=True).splitlines():
        target=FROZEN/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(subprocess.check_output(['git','show','6852a20:'+name],cwd=BASE))
reconstruct();sys.path.insert(0,str(FROZEN))
import gflo.browser as b
rows=[]
def record(name,fn):
    try: value=fn();rows.append({'case':name,'observed':value})
    except Exception as e: rows.append({'case':name,'error':type(e).__name__,'message':str(e)})
def frame(files=None,status='passed'):
    if files is None:files={'screen-1.png':b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II',1280,800),'trace.zip':b'PK\x03\x04opaque','events.json':b'[]'}
    return json.dumps({'status':status,'files':[{'name':n,'size':len(d),'sha256':b.digest(d)} for n,d in files.items()]}).encode()+b'\n'+b''.join(files.values())
def fixture(root):
    def executor(spec,out,**kw):
        assert (store.root/'.cleanup-required').is_file()
        out.write(frame());return {'exit_code':0,'reason':None,'diagnostics':'','transport_errors':[],'facts':{'cleanup':{'confirmed':True},'failure':None}}
    store=b.BrowserStore(root/'store',executor=executor)
    stage=pathlib.Path(tempfile.mkdtemp(prefix='.stage-',dir=store.root));(stage/'support').mkdir();b.freeze(stage/'support')
    support=store._commit(stage,{'kind':'support','packages':b.PACKAGES,'tree_sha256':b.tree_hash(stage/'support'),'image':b.BROWSER_IMAGE,'app_image':b.NODE_IMAGE,'seccomp_sha256':b.SECCOMP})['id']
    for folder,file in [('app','server.cjs'),('checks','journey.cjs')]:
        (root/folder).mkdir();(root/folder/file).write_text('trusted fixture')
    (root/'seed.json').write_text('{}')
    approval={'app':str(root/'app'),'checks':str(root/'checks'),'seed':str(root/'seed.json'),'case':'security','support':support}
    return store,approval,executor
def faults():
    for mode in ['control','sync-failure','rename-failure','late-cancel','cleanup-uncertain','executor-exception','transport-error','exit125']:
        with tempfile.TemporaryDirectory(dir=PRIVATE) as td:
            root=pathlib.Path(td);store,approval,executor=fixture(root)
            prior=store.check(approval);cancel=[False];error=None;result=None
            def sync(path):
                if mode=='sync-failure':raise OSError('controlled sync failure')
                if mode=='late-cancel':cancel[0]=True
            def pair(*args,**kw):
                if mode=='executor-exception':raise OSError('controlled guardian error')
                value=executor(*args,**kw)
                if mode=='cleanup-uncertain':value['facts']['cleanup']['confirmed']=False
                if mode=='transport-error':value['transport_errors']=['controlled copy error']
                if mode=='exit125':value['exit_code']=125
                return value
            store.pair=pair
            with patch.object(b,'sync_directory',sync):
                try:
                    if mode=='rename-failure':
                        with patch.object(pathlib.Path,'rename',side_effect=OSError('controlled rename error')):result=store.check(approval,cancelled=lambda:cancel[0])
                    else:result=store.check(approval,cancelled=lambda:cancel[0])
                except Exception as e:error=type(e).__name__+': '+str(e)
            record(mode,lambda:{'returned_status':result['receipt']['outcome']['status'] if result else None,'error':error,'cancelled':cancel[0],'prior_good':store.inspect(prior['id'])['id']==prior['id'],'cleanup_fence':(store.root/'.cleanup-required').exists(),'result_records':len([p for p in store.root.iterdir() if len(p.name)==64])-1})
    for name,raw in [('frame-control',frame()),('trailing',frame()+b'x'),('truncated',frame()[:-1]),('missing',frame({})),('traversal',frame({'../x':b'x'})),('png-oversize',frame({'screen-1.png':b'x'*(2*1024*1024+1)})),('events512',frame({'events.json':json.dumps([{}]*512).encode()},'failed')),('events513',frame({'events.json':json.dumps([{}]*513).encode()},'failed')),('metadata-oversize',b'x'*65537)]:
        with tempfile.TemporaryDirectory(dir=PRIVATE) as td:
            record(name,lambda:b.receive(io.BytesIO(raw),pathlib.Path(td)/'artifacts')[0]['status'])
    for mode in ['regular','symlink','hardlink','fifo','deep','bytes']:
        with tempfile.TemporaryDirectory(dir=PRIVATE) as td:
            root=pathlib.Path(td);source=root/'input';source.mkdir();(source/'file').write_text('ok')
            if mode=='symlink':(source/'link').symlink_to('file')
            if mode=='hardlink':os.link(source/'file',source/'link')
            if mode=='fifo':os.mkfifo(source/'pipe')
            if mode=='deep':(source/('x'*120)/('y'*120)).mkdir(parents=True)
            if mode=='bytes':(source/'file').write_bytes(b'x'*65)
            record('input-'+mode,lambda:b.snapshot(source,root/'copy',10,64))
    (OUT/'fault-results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))
if __name__=='__main__':faults()
