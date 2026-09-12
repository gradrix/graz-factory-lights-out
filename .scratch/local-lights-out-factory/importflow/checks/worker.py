import contextlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path
from blobs import put_blob
from jobs import Store
from worker import run_once,csv_handler,main

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)/'blobs';path=Path(folder)/'db';store=Store(path)
    payload=put_blob(root,[b'label,quantity\nx,2\nx,-1\n'])
    job=store.submit('csv','inventory_csv',payload)
    assert run_once(store,root,{'inventory_csv':csv_handler},now=10)
    assert store.get(job['id'])['result']==[dict(label='x',quantity=1)]
    other=store.submit('other','length',payload)
    assert run_once(store,root,{'length':lambda stream:len(stream.read())},now=11)
    assert store.get(other['id'])['result']==len(b'label,quantity\nx,2\nx,-1\n')
    unknown=store.submit('unknown','unknown',payload)
    assert run_once(store,root,{},now=12)
    assert store.get(unknown['id'])['status']=='failed' and store.get(unknown['id'])['error']
    bad=store.submit('bad','inventory_csv',put_blob(root,[b'label,quantity\nx,"1']))
    run_once(store,root,{'inventory_csv':csv_handler},now=13)
    assert store.get(bad['id'])['status']=='failed' and 'row 2' in store.get(bad['id'])['error']
    # Process dies after claim inside handler; next process must reclaim the job.
    crash=store.submit('crash','die',payload)
    script="import os,sys; from jobs import Store; from worker import run_once; run_once(Store(sys.argv[1]),sys.argv[2],{'die':lambda stream:os._exit(17)},now=20,ttl=1)"
    result=subprocess.run([sys.executable,'-c',script,str(path),str(root)],capture_output=True,text=True)
    assert result.returncode==17,(result.returncode,result.stderr)
    old=store.get(crash['id']);assert old['status']=='running'
    assert run_once(Store(path),root,{'die':lambda stream:{'recovered':True}},now=21)
    assert store.get(crash['id'])['result']=={'recovered':True}
    assert not store.finish(crash['id'],old['token'],21,result={'wrong':True})
    assert not run_once(store,root,{},now=30)
    cli=store.submit('cli','inventory_csv',payload)
    result=subprocess.run([sys.executable,'-m','worker','--db',str(path),'--blobs',str(root),'--once'],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert store.get(cli['id'])['status']=='succeeded'
    for argv,code in (([],2),(['--help'],0),(['--db',str(path),'--blobs',str(root),'--poll','nan'],2)):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            actual=main(argv)
        assert actual==code,(argv,actual,code)
print('worker-ok')
