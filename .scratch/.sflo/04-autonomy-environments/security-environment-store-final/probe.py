import copy
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import signal
import stat
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
CANDIDATE='edc7d7180d89599b83fe4fd507919e6e08b414b6'
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
    incoming=[]
    def fail_directory(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode) and os.readlink(f'/proc/self/fd/{fd}')==str(store.root):
            incoming.extend(identity for identity in ids(store) if identity!=env.id)
            assert len(incoming)==1
            error=expect_error(lambda:EnvironmentStore(store.root).resolve(incoming[0]))
            assert 'owns' in error
            observed.append(error)
            raise OSError('controlled post-rename directory fsync failure')
        original_fsync(fd)
    with patch('gflo.environment.os.fsync',side_effect=fail_directory):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    unchanged(store,env,raw)
    assert ids(store)==[env.id]
    assert not list(store.root.glob('.prepare-*'))
    failed=expect_error(lambda:store.resolve(incoming[0]))
    return {'publication_error':error,'failed_candidate_id':incoming[0],'failed_candidate_resolvable':False,'reader_blocked_during_publication':bool(observed),'resolution_error':failed}
record('post-rename-fsync-failure-retires-candidate',lambda:with_store(post_rename_failure))

def final_verification_failure(store,tmp):
    env,raw=good(store)
    resolver=store._resolve
    incoming=[]
    def fail_new(identifier,expected_hash=None,**kwargs):
        if identifier!=env.id:
            incoming.append(identifier)
            raise OSError('controlled final verification failure')
        return resolver(identifier,expected_hash,**kwargs)
    with patch.object(store,'_resolve',side_effect=fail_new):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    assert incoming
    assert ids(store)==[env.id]
    assert not list(store.root.glob('.prepare-*'))
    unchanged(store,env,raw)
    return {'error':error,'failed_resolution':expect_error(lambda:store.resolve(incoming[0]))}
record('post-rename-final-verification-failure-retires-candidate',lambda:with_store(final_verification_failure))

def retired_cleanup_failure(store,tmp):
    env,raw=good(store)
    original_fsync=os.fsync
    incoming=[]
    def fail_directory(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode) and os.readlink(f'/proc/self/fd/{fd}')==str(store.root):
            incoming.extend(identity for identity in ids(store) if identity!=env.id)
            raise OSError('controlled durability failure')
        original_fsync(fd)
    with patch('gflo.environment.os.fsync',side_effect=fail_directory), patch('gflo.environment.discard',side_effect=OSError('controlled retired cleanup failure')):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
        assert 'retired cleanup' in error
        assert ids(store)==[env.id]
        assert len(list(store.root.glob('.prepare-*')))==1
        assert 'missing' in expect_error(lambda:store.resolve(incoming[0]))
        assert 'retired cleanup' in expect_error(lambda:put(store))
    unchanged(store,env,raw)
    store.remove_private_staging()
    assert not list(store.root.glob('.prepare-*'))
    return {'error':error,'failed_candidate_resolvable':False,'reconciled':True}
record('cleanup-failure-after-retirement-remains-private',lambda:with_store(retired_cleanup_failure))

def shared_readers(store,tmp):
    env,raw=good(store)
    with store.locked(shared=True):
        assert EnvironmentStore(store.root).resolve(env.id).id==env.id
        error=expect_error(lambda:put(store))
        assert 'owns' in error
    unchanged(store,env,raw)
    return {'shared_reader_succeeded':True,'publisher_refused':error}
record('concurrent-shared-readers-block-publisher',lambda:with_store(shared_readers))

def retirement_rename_failure(store,tmp):
    env,raw=good(store)
    rename=Path.rename
    fsync=os.fsync
    incoming=[]
    def fail_directory(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode) and os.readlink(f'/proc/self/fd/{fd}')==str(store.root):
            incoming.extend(identity for identity in ids(store) if identity!=env.id)
            raise OSError('controlled publication durability failure')
        fsync(fd)
    def fail_retirement(path,target):
        if len(path.name)==64 and Path(target).name.startswith('.prepare-'):
            raise OSError('controlled retirement rename failure')
        return rename(path,target)
    with patch('gflo.environment.os.fsync',side_effect=fail_directory), patch('gflo.environment.Path.rename',autospec=True,side_effect=fail_retirement):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    assert error=='controlled retirement rename failure'
    resolve_error=expect_error(lambda:EnvironmentStore(store.root).resolve(incoming[0]))
    assert 'pending' in resolve_error
    retry=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    assert 'pending' in retry
    unchanged(store,env,raw)
    return {'error':error,'failed_candidate_id':incoming[0],'failed_candidate_resolvable':False,'resolution_error':resolve_error,'same_id_retry':retry,'baseline_unchanged':True}
record('retirement-rename-failure-leaves-non-runnable-pending-candidate',lambda:with_store(retirement_rename_failure))

def marker_removal_failure(store,tmp):
    env,raw=good(store)
    unlink=Path.unlink
    identifiers=[]
    def fail_pending(path,*args,**kwargs):
        if path.name=='pending' and len(path.parent.name)==64:
            identifiers.append(path.parent.name)
            raise OSError('controlled marker removal failure')
        return unlink(path,*args,**kwargs)
    with patch('gflo.environment.Path.unlink',autospec=True,side_effect=fail_pending):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    assert error=='controlled marker removal failure'
    assert len(identifiers)==1
    assert ids(store)==[env.id]
    assert not list(store.root.glob('.prepare-*'))
    unchanged(store,env,raw)
    return {'error':error,'failed_resolution':expect_error(lambda:store.resolve(identifiers[0]))}
record('marker-removal-failure-retires-candidate',lambda:with_store(marker_removal_failure))

def cancel_during_final_sync(store,tmp):
    env,raw=good(store)
    fsync=os.fsync
    cancelled=[False]
    identifiers=[]
    def cancel(fd):
        fsync(fd)
        if stat.S_ISDIR(os.fstat(fd).st_mode) and os.readlink(f'/proc/self/fd/{fd}')==str(store.root):
            cancelled[0]=True
            identifiers.extend(identity for identity in ids(store) if identity!=env.id)
    with patch('gflo.environment.os.fsync',side_effect=cancel):
        error=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'},cancelled=lambda:cancelled[0]))
    assert 'cancelled' in error
    assert identifiers
    assert ids(store)==[env.id]
    assert not list(store.root.glob('.prepare-*'))
    unchanged(store,env,raw)
    return {'error':error,'failed_resolution':expect_error(lambda:store.resolve(identifiers[0]))}
record('cancellation-during-final-root-sync-revokes-publication',lambda:with_store(cancel_during_final_sync))

def owner_exit(store,tmp):
    env,raw=good(store)
    pid=os.fork()
    if pid==0:
        fsync=os.fsync
        def exit_at_root(fd):
            fsync(fd)
            if stat.S_ISDIR(os.fstat(fd).st_mode) and os.readlink(f'/proc/self/fd/{fd}')==str(store.root):os.kill(os.getpid(),signal.SIGKILL)
        try:
            with patch('gflo.environment.os.fsync',side_effect=exit_at_root):
                put(store,verify=lambda _: {'passed':True,'output':'candidate H'})
        except BaseException:os._exit(74)
        os._exit(75)
    _,status=os.waitpid(pid,0)
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGKILL
    failed=[identity for identity in ids(store) if identity!=env.id]
    assert len(failed)==1
    error=expect_error(lambda:EnvironmentStore(store.root).resolve(failed[0]))
    assert 'pending' in error
    assert (store.root/failed[0]/'pending').is_file()
    unchanged(store,env,raw)
    retry=expect_error(lambda:put(store,verify=lambda _: {'passed':True,'output':'candidate H'}))
    assert 'pending' in retry
    return {'child_signal':'SIGKILL','failed_candidate_id':failed[0],'resolution_error':error,'same_id_retry':retry,'baseline_unchanged':True}
record('owner-sigkill-after-rename-leaves-persistent-pending-fence',lambda:with_store(owner_exit))

def committed_has_no_marker(store,tmp):
    env,raw=good(store)
    assert not (store.root/env.id/'pending').exists()
    assert EnvironmentStore(store.root).resolve(env.id).id==env.id
    assert put(store).id==env.id
    unchanged(store,env,raw)
    return {'pending_absent':True,'fresh_resolver_succeeded':True,'same_id_reuse':True}
record('successful-commit-clears-marker-and-supports-reuse',lambda:with_store(committed_has_no_marker))

result={'candidate':CANDIDATE,'python':platform.python_version(),'source_sha256':hashlib.sha256((FROZEN/'gflo/environment.py').read_bytes()).hexdigest(),'pass':sum(r['status']=='pass' for r in RESULTS),'fail':sum(r['status']=='fail' for r in RESULTS),'results':RESULTS}
(FROZEN/'rerun-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
for row in RESULTS:
    if row['status']=='fail' or row['probe'].startswith(('post-rename','retirement')):print(json.dumps(row))
print(f'Rerun evidence: {FROZEN / "rerun-results.json"}',flush=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_environment.py','-v'],cwd=FROZEN,check=True)
sys.exit(1 if result['fail'] else 0)
