import json
import subprocess
import sys
import tempfile
from pathlib import Path
from jobs import Store

fields={'id','key','kind','payload','status','attempts','token','lease_until','result','error'}
with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'jobs.db';store=Store(path,max_pending=1)
    job=store.submit('one','inventory_csv','a'*64)
    assert set(job)==fields and job['status']=='queued' and type(job['attempts']) is int and job['attempts']==0,job
    assert all(job[k] is None for k in ('token','lease_until','result','error'))
    assert Store(path).submit('one','inventory_csv','a'*64)==job
    for args in [('one','inventory_csv','b'*64),('one','other','a'*64),('x\n','kind','a'*64),('x','kind\n','a'*64),('x','kind','a'*64+'\n')]:
        try: store.submit(*args)
        except ValueError: pass
        else: raise AssertionError(('invalid/conflicting submit',args))
    try: store.submit('two','kind','b'*64)
    except OverflowError: pass
    else: raise AssertionError('capacity ignored')
    assert store.submit('one','inventory_csv','a'*64)==job
    first=store.claim(10,ttl=1)
    assert first['id']==job['id'] and first['attempts']==1 and first['lease_until']==11
    assert store.claim(10.5,ttl=1) is None
    assert not store.finish(first['id'],first['token'],11,result=1), 'expired worker committed'
    second=Store(path).claim(11,ttl=5)
    assert second['attempts']==2 and second['token']!=first['token']
    assert not store.finish(first['id'],first['token'],12,result=1), 'stale worker committed'
    assert store.finish(second['id'],second['token'],12,result={'value':2})
    assert not store.finish(second['id'],second['token'],12,result={'value':3})
    done=Store(path).get(job['id']);assert done['result']=={'value':2} and done['status']=='succeeded'
    assert done['token'] is None and done['lease_until'] is None
    assert store.get('unknown') is None
    abandoned=store.submit('abandoned','kind','b'*64)
    for n in range(3):
        claimed=store.claim(20+n,ttl=1);assert claimed['attempts']==n+1
    assert store.claim(23) is None
    failed=store.get(abandoned['id']);assert failed['status']=='failed' and failed['error']
    for now in (True,float('nan'),float('inf'),-1):
        try: store.claim(now)
        except ValueError: pass
        else: raise AssertionError(('bad clock',now))
    for kwargs in ({},{'result':1,'error':'bad'},{'result':float('nan')},{'result':'x'*1048577},{'error':''}):
        try: store.finish('unknown','token',30,**kwargs)
        except ValueError: pass
        else: raise AssertionError(('bad completion',repr(kwargs)[:80]))
    # Real independent processes contend for one idempotency key.
    submit="from jobs import Store; import sys; print(Store(sys.argv[1]).submit('race','kind','c'*64)['id'])"
    procs=[subprocess.Popen([sys.executable,'-c',submit,str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(8)]
    identities=[]
    for proc in procs:
        out,err=proc.communicate(timeout=15);assert proc.returncode==0,err;identities.append(out.strip())
    assert len(set(identities))==1,identities
    claim="from jobs import Store; import sys,json; print(json.dumps(Store(sys.argv[1]).claim(100,ttl=10)))"
    procs=[subprocess.Popen([sys.executable,'-c',claim,str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(8)]
    winners=[]
    for proc in procs:
        out,err=proc.communicate(timeout=15);assert proc.returncode==0,err;winners.append(json.loads(out))
    assert sum(x is not None for x in winners)==1,winners
print('jobs-ok')
