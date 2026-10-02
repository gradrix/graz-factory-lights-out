import copy
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
CANDIDATE='1506abf89cceb8e9adf1a446caf9d92ad53c29c2'
REPO=Path(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--show-toplevel'],text=True).strip())
FROZEN=REPO/'.gflo/security-environment-store'/CANDIDATE
files=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only',CANDIDATE,'gflo/__init__.py','gflo/artifacts.py','gflo/environment.py','tests/test_environment.py','evaluations/environment-artifacts'],text=True).splitlines()
for relative in files:
    path=FROZEN/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(subprocess.check_output(['git','-C',str(REPO),'show',f'{CANDIDATE}:{relative}']))
sys.path.insert(0,str(FROZEN))
from gflo.environment import EnvironmentStore, discard

META={'profile':'python-stdlib','image':'sha256:'+'a'*64,'platform':'linux/amd64','recipe_sha256':'b'*64,'locks':{},'runtime':{'python':'3.12.13'}}
CORPUS=FROZEN/'evaluations/environment-artifacts'
DATA=(CORPUS/'archives/00-valid-package.tar').read_bytes()
RESULTS=[]
def record(name,call):
    try:RESULTS.append({'probe':name,'status':'pass','detail':call()})
    except Exception as error:RESULTS.append({'probe':name,'status':'fail','error':repr(error)})

def smoke(path):return {'passed':True,'output':'controlled trusted verification'}
def put(store,data=DATA,verify=smoke,**kwargs):return store.publish(io.BytesIO(data),META,verify,**kwargs)
def ids(store):return sorted(p.name for p in store.root.iterdir() if len(p.name)==64)
def good(store):
    env=put(store)
    raw=(store.root/env.id/'receipt.json').read_bytes()
    return env,raw
def unchanged(store,env,raw):
    assert store.resolve(env.id,env.receipt_hash).id==env.id
    assert (store.root/env.id/'receipt.json').read_bytes()==raw

def with_store(fn):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/'store'
        store=EnvironmentStore(root)
        try:return fn(store,Path(tmp))
        finally:
            if root.is_dir() and not root.is_symlink():discard(root)

def expect_error(fn):
    try:fn()
    except (ValueError,OSError) as error:return str(error)
    raise AssertionError('unexpected success')

def valid(store,tmp):
    env,raw=good(store)
    assert store.resolve(env.id,env.receipt_hash)==env
    assert put(store).id==env.id
    assert ids(store)==[env.id]
    assert not list(store.root.glob('.prepare-*'))
    receipt=json.loads(raw)
    assert receipt['metadata']==META
    assert env.dependencies==store.root/env.id/'deps'
    return {'id':env.id,'tree_sha256':receipt['tree_sha256'],'files':[str(p.relative_to(env.dependencies)) for p in env.dependencies.rglob('*')]}
record('valid-idempotent-controller-path-control',lambda:with_store(valid))

for kind in ['bytes','remove','add','rename','executable-mode','writable-mode','directory-mode','root-mode','file-symlink','directory-symlink','fifo','receipt-image','receipt-locks','receipt-tree','receipt-mode','receipt-symlink','publication-mode','expected-hash']:
    def tamper(store,tmp,kind=kind):
        env,raw=good(store)
        files=[p for p in env.dependencies.rglob('*') if p.is_file()]
        target=files[0]
        target.parent.chmod(0o755)
        if kind=='bytes':target.chmod(0o644);target.write_bytes(b'changed');target.chmod(0o444)
        elif kind=='remove':target.unlink()
        elif kind=='add':
            extra=target.parent/'extra';extra.write_bytes(b'extra');extra.chmod(0o444)
        elif kind=='rename':target.rename(target.with_name('renamed'))
        elif kind=='executable-mode':target.chmod(0o555 if stat.S_IMODE(target.stat().st_mode)==0o444 else 0o444)
        elif kind=='writable-mode':target.chmod(0o644)
        elif kind=='directory-mode':pass
        elif kind=='root-mode':env.dependencies.chmod(0o700)
        elif kind=='file-symlink':
            sentinel=tmp/'sentinel';sentinel.write_text('private');target.unlink();target.symlink_to(sentinel)
        elif kind=='directory-symlink':
            extra=target.parent/'linked';extra.symlink_to(tmp,target_is_directory=True)
        elif kind=='fifo':os.mkfifo(target.parent/'pipe')
        elif kind.startswith('receipt-'):
            receipt=store.root/env.id/'receipt.json'
            if kind=='receipt-mode':receipt.chmod(0o644)
            elif kind=='receipt-symlink':
                sentinel=tmp/'receipt-copy';sentinel.write_bytes(raw);receipt.unlink();receipt.symlink_to(sentinel)
            else:
                value=json.loads(raw)
                if kind=='receipt-image':value['metadata']['image']='sha256:'+'c'*64
                if kind=='receipt-locks':value['metadata']['locks']={'fake':'d'*64}
                if kind=='receipt-tree':value['tree_sha256']='e'*64
                receipt.chmod(0o644);receipt.write_text(json.dumps(value));receipt.chmod(0o444)
        elif kind=='publication-mode':(store.root/env.id).chmod(0o755)
        if kind!='directory-mode':target.parent.chmod(0o555)
        return expect_error(lambda:store.resolve(env.id,'f'*64 if kind=='expected-hash' else env.receipt_hash))
    record('tamper/'+kind,lambda kind=kind:with_store(lambda store,tmp:tamper(store,tmp,kind)))

for identifier in ['../outside','/tmp/outside','a'*63,'A'*64,'a'*64+'/deps',None]:
    record('id/'+repr(identifier),lambda identifier=identifier:with_store(lambda store,tmp:expect_error(lambda:store.resolve(identifier))))

manifest=json.loads((CORPUS/'manifest.json').read_text())
for case in manifest['archive_cases']:
    if case['expected_result']!='reject' or case['id'][:2] in ('19','20','22'):continue
    def failed_archive(store,tmp,case=case):
        env,raw=good(store)
        error=expect_error(lambda:put(store,(CORPUS/case['archive']).read_bytes()))
        unchanged(store,env,raw)
        assert ids(store)==[env.id]
        assert not list(store.root.glob('.prepare-*'))
        return error
    record('failed-archive/'+case['id'],lambda case=case:with_store(lambda store,tmp:failed_archive(store,tmp,case)))

for phase in ['initial','after-transport','smoke','final-fence']:
    def cancel(store,tmp,phase=phase):
        env,raw=good(store)
        flag=[phase=='initial']
        calls=[0]
        class Stream(io.BytesIO):
            def read(self,size):
                assert phase!='initial','initial cancellation consumed input'
                value=super().read(size)
                if not value and phase=='after-transport':flag[0]=True
                return value
        def verify(path):
            calls[0]+=1
            if phase=='smoke':flag[0]=True
            return smoke(path)
        fsync=os.fsync
        def injected(fd):
            fsync(fd)
            if phase=='final-fence' and stat.S_ISREG(os.fstat(fd).st_mode) and calls[0]:flag[0]=True
        with patch('gflo.environment.os.fsync',side_effect=injected):
            error=expect_error(lambda:store.publish(Stream(DATA),META,verify,cancelled=lambda:flag[0]))
        assert 'cancelled' in error
        unchanged(store,env,raw)
        assert ids(store)==[env.id]
        assert not list(store.root.glob('.prepare-*'))
        return {'error':error,'smoke_calls':calls[0]}
    record('cancel/'+phase,lambda phase=phase:with_store(lambda store,tmp:cancel(store,tmp,phase)))

for action in ['failed-smoke','smoke-exception','smoke-tree-mutation','receipt-too-large','pre-rename-failure']:
    def bad_check(store,tmp,action=action):
        env,raw=good(store)
        def verify(path):
            if action=='failed-smoke':return {'passed':False}
            if action=='smoke-exception':raise ValueError('controlled smoke failure')
            if action=='smoke-tree-mutation':
                target=next(p for p in path.rglob('*') if p.is_file());target.chmod(0o644);target.write_bytes(b'changed');target.chmod(0o444)
            if action=='receipt-too-large':return {'passed':True,'output':'x'*65536}
            return {'passed':True,'output':'candidate H'}
        if action=='pre-rename-failure':
            with patch('gflo.environment.Path.rename',side_effect=OSError('controlled rename failure')):error=expect_error(lambda:put(store,verify=verify))
        else:error=expect_error(lambda:put(store,verify=verify))
        unchanged(store,env,raw)
        assert ids(store)==[env.id]
        assert not list(store.root.glob('.prepare-*'))
        return error
    record('failure/'+action,lambda action=action:with_store(lambda store,tmp:bad_check(store,tmp,action)))

def cleanup_failure(store,tmp):
    env,raw=good(store)
    with patch('gflo.environment.discard',side_effect=OSError('controlled cleanup failure')):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':False}))
        assert error=='controlled cleanup failure'
        stages=list(store.root.glob('.prepare-*'))
        assert len(stages)==1
        assert ids(store)==[env.id]
        retry=expect_error(lambda:put(store))
        assert retry=='controlled cleanup failure'
        unchanged(store,env,raw)
    store.remove_private_staging()
    assert not list(store.root.glob('.prepare-*'))
    unchanged(store,env,raw)
    return {'error':error,'retry':retry,'reconciled':True}
record('cleanup-failure-blocks-retry-until-reconciled',lambda:with_store(cleanup_failure))

def lock(store,tmp):
    with store.locked():
        error=expect_error(lambda:put(store))
        assert 'owns' in error
    assert not ids(store)
    return error
record('concurrent-preparation-refused',lambda:with_store(lock))

def publication_symlink(store,tmp):
    env,raw=good(store)
    peer=EnvironmentStore(tmp/'peer')
    h=put(peer,verify=lambda _: {'passed':True,'output':'candidate H'})
    sentinel=tmp/'sentinel';sentinel.mkdir(mode=0o700);(sentinel/'keep').write_bytes(b'unchanged')
    destination=store.root/h.id;destination.symlink_to(sentinel,target_is_directory=True)
    error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    assert destination.is_symlink()
    assert (sentinel/'keep').read_bytes()==b'unchanged'
    unchanged(store,env,raw)
    assert not list(store.root.glob('.prepare-*'))
    discard(peer.root)
    return error
record('preexisting-final-destination-symlink-preserved',lambda:with_store(publication_symlink))

def post_rename_failure(store,tmp):
    env,raw=good(store)
    original_fsync=os.fsync
    observed=[]
    def fail_directory(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            incoming=[identity for identity in ids(store) if identity!=env.id]
            assert len(incoming)==1
            observed.append(EnvironmentStore(store.root).resolve(incoming[0]).id)
            raise OSError('controlled post-rename directory fsync failure')
        original_fsync(fd)
    with patch('gflo.environment.os.fsync',side_effect=fail_directory):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    unchanged(store,env,raw)
    others=[identity for identity in ids(store) if identity!=env.id]
    assert len(others)==1,'expected reproduction of leaked publication'
    resolved=store.resolve(others[0])
    assert resolved.id==others[0]
    return {'publication_error':error,'failed_candidate_id':resolved.id,'failed_candidate_resolvable':True,'resolvable_while_publish_lock_held':observed==[resolved.id],'baseline_unchanged':True,'private_staging_left':len(list(store.root.glob('.prepare-*')))}
record('post-rename-fsync-failure-publishes-resolvable-candidate',lambda:with_store(post_rename_failure))

result={'candidate':CANDIDATE,'python':platform.python_version(),'source_sha256':hashlib.sha256((FROZEN/'gflo/environment.py').read_bytes()).hexdigest(),'pass':sum(r['status']=='pass' for r in RESULTS),'fail':sum(r['status']=='fail' for r in RESULTS),'results':RESULTS}
(FROZEN/'rerun-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
for row in RESULTS:
    if row['status']=='fail' or row['probe'].startswith('post-rename'):print(json.dumps(row))
print(f'Rerun evidence: {FROZEN / "rerun-results.json"}',flush=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_environment.py','-v'],cwd=FROZEN,check=True)
sys.exit(1 if result['fail'] else 0)
