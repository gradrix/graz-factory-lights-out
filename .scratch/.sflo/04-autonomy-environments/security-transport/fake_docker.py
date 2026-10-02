#!/usr/bin/env python3
"""Test-owned process executor; never invokes Docker or container APIs."""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import threading

root=Path(os.environ['GFLO_SECURITY_FAKE_DOCKER'])
args=sys.argv[1:]
mode=os.environ.get('GFLO_SECURITY_FAKE_MODE','')
def event(kind,**kw):
    with (root/'events.jsonl').open('a') as output:output.write(json.dumps({'event':kind,'time':time.monotonic(),**kw})+'\n')
def lock():
    stream=(root/'daemon.lock').open('a');fcntl.flock(stream,fcntl.LOCK_EX);return stream
def state(name):return root/(name+'.json')
event('command',args=args,pid=os.getpid())
if args[0]=='create':
    name=args[args.index('--name')+1]
    if mode=='create-fails':
        print('controlled create failure',file=sys.stderr);sys.exit(17)
    if mode=='create-delayed':time.sleep(.4)
    with lock():state(name).write_text(json.dumps({'args':args,'name':name}))
    event('created',name=name)
    print(name)
elif args[0]=='inspect':
    name=args[1]
    if mode=='inspect-fails':sys.exit(18)
    value=json.loads(state(name).read_text())
    spec={'Image':'sha256:'+'a'*64,'HostConfig':{'Runtime':'runc','NetworkMode':'none','ReadonlyRootfs':True,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],'Memory':134217728,'MemorySwap':134217728,'NanoCpus':1000000000,'PidsLimit':16,'ShmSize':16777216,'Tmpfs':{'/tmp':'rw,nosuid,nodev,size=8m'},'Devices':[],'DeviceRequests':None},'Config':{'User':'1234:1234','Env':['HOME=/tmp','VISIBLE_FACT=from-inspect'],'WorkingDir':'/workspace'},'Mounts':[{'Type':'bind','Source':'/controlled/snapshot','Destination':'/opt/deps','RW':False}]}
    (root/'inspection-input.json').write_text(json.dumps(spec))
    print(json.dumps([spec]))
elif args[0]=='start':
    name=args[-1]
    with lock():
        if not state(name).exists():sys.exit(19)
        value=json.loads(state(name).read_text())
        command=value['args']
        image=next(i for i,a in enumerate(command) if a.startswith('sha256:'))
        executor=subprocess.Popen(command[image+1:],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        value['executor']=executor.pid
        state(name).write_text(json.dumps(value))
        event('started',name=name,executor=executor.pid)
    def relay(source,destination):
        try:
            while True:
                block=source.read(4096)
                if not block:break
                destination.write(block);destination.flush()
        except BrokenPipeError:pass
    readers=[threading.Thread(target=relay,args=(executor.stdout,sys.stdout.buffer),daemon=True),threading.Thread(target=relay,args=(executor.stderr,sys.stderr.buffer),daemon=True)]
    for reader in readers:reader.start()
    result=executor.wait()
    for reader in readers:reader.join()
    event('executor-exit',name=name,code=result)
    sys.exit(result if result>=0 else 128-result)
elif args[0]=='rm':
    name=args[-1]
    if mode=='cleanup-fails':
        event('cleanup-failed',name=name)
        print('controlled daemon cleanup failure',file=sys.stderr);sys.exit(23)
    with lock():
        path=state(name)
        if path.exists():
            value=json.loads(path.read_text())
            if 'executor' in value:
                try:os.killpg(value['executor'],signal.SIGKILL)
                except ProcessLookupError:pass
            path.unlink()
        event('removed',name=name)
else:
    print('unsupported fake docker operation',file=sys.stderr);sys.exit(99)
