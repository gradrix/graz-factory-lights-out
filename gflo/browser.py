"""One frozen local Node application, one supervised Playwright journey."""
from contextlib import contextmanager
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import struct
import tarfile
import tempfile
import time

from .documents import active, checked_file, digest, encoded, sync_directory, utc, write_file
from .environment import discard, tree_hash as environment_tree_hash
from .artifacts import ArchiveLimits
from .prepare import NODE_IMAGE

BROWSER_IMAGE = 'sha256:2c1f4e0fd6450f43ddb46d60c2a6df30855a8588e165b1f2559fb0eda8d7ff35'
RECIPE = Path(__file__).parent / 'recipes' / 'browser'
SECCOMP = '322b86b4f7f5b597ed6a9c2cfd6193a4b249a51c8bc9cfba8ff1a485070b24e8'
PACKAGES = {'playwright': '195a5ee9bfed7c6e9c03965950e32e5e4dbedaa02e740e5a530eb4b87dae050c',
            'playwright-core': '208593d4e1bcd8f8fe5f869cad1cc332dc7f1d70dc1d58c102dc3ac36e30f26c'}
LIMIT = 24 * 1024 * 1024
HEX = re.compile('[0-9a-f]{64}')


def installed_images():
    facts={}
    for name,image in [('app',NODE_IMAGE),('browser',BROWSER_IMAGE)]:
        result=subprocess.run(['docker','image','inspect',image],capture_output=True,text=True,timeout=15)
        if result.returncode:
            raise ValueError('Pinned browser/app image must be preinstalled; no pull fallback')
        value=json.loads(result.stdout)[0]
        if value['Id']!=image or value.get('Architecture')!='amd64' or value.get('Os')!='linux':
            raise ValueError('Unsupported browser image/platform')
        facts[name]={'id':value['Id'],'platform':'linux/amd64','environment':value['Config'].get('Env',[])}
    return facts


def tree_hash(root, limits=ArchiveLimits()):
    identity=environment_tree_hash(root,limits)
    for path in root.rglob('*'):
        info=path.lstat()
        if stat.S_ISREG(info.st_mode) and info.st_nlink!=1:
            raise ValueError('Browser snapshot hard link changed')
    return identity


def freeze(root):
    for path in root.rglob('*'):
        path.chmod(0o555 if path.is_dir() else 0o444)
    root.chmod(0o555)


def snapshot(source, destination, entries, size):
    """Copy approved regular inputs, rejecting changes during the copy."""
    source, destination = Path(source).absolute(), Path(destination)
    if any(p.is_symlink() for p in (source, *source.parents)) or not source.is_dir():
        raise ValueError('Browser inputs require a regular directory without link ancestors')
    def listing():
        paths=[]
        for path in source.rglob('*'):
            paths.append(path)
            if len(paths)>entries:raise ValueError('Browser input entry limit')
        return sorted(paths)
    paths=listing()
    destination.mkdir(mode=0o700)
    total = 0
    identities = {}
    for path in paths:
        relative = path.relative_to(source)
        if len(str(relative).encode()) > 240 or '\\' in str(relative):
            raise ValueError('Browser input path limit')
        before = path.lstat()
        identities[str(relative)] = (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        target = destination / relative
        if stat.S_ISDIR(before.st_mode):
            target.mkdir()
        elif stat.S_ISREG(before.st_mode) and before.st_nlink == 1:
            total += before.st_size
            if total > size:
                raise ValueError('Browser input byte limit')
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                    raise ValueError('Browser input changed during copy')
                data = stream.read(before.st_size + 1)
            if len(data) != before.st_size:
                raise ValueError('Browser input changed size')
            write_file(target, data)
        else:
            raise ValueError('Browser inputs reject links and special files')
    if sorted(str(p.relative_to(source)) for p in listing()) != sorted(identities):
        raise ValueError('Browser input entries changed')
    for relative, identity in identities.items():
        info = (source / relative).lstat()
        if identity != (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns):
            raise ValueError('Browser input changed during copy')
    freeze(destination)
    return tree_hash(destination, ArchiveLimits(entries=entries, expanded_bytes=size))


def support_archive(path, destination, expected):
    path = Path(path)
    if any(p.is_symlink() for p in (path,*path.absolute().parents)) or not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Invalid offline browser archive')
    with path.open('rb') as stream:raw=stream.read(8*1024*1024+1)
    if len(raw)>8*1024*1024:raise ValueError('Browser archive byte limit')
    if digest(raw) != expected:
        raise ValueError('Browser package hash mismatch')
    # Trusted pinned archive, still enforce finite regular-file extraction.
    seen, total = set(), 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for index, member in enumerate(archive):
            name = PurePosixPath(member.name)
            if index >= 2048 or name.parts[:1] != ('package',) or '..' in name.parts or name.is_absolute():
                raise ValueError('Invalid browser package archive path/count')
            relative = PurePosixPath(*name.parts[1:])
            if str(name) != member.name.rstrip('/') or '\\' in member.name or str(relative) in seen:
                raise ValueError('Ambiguous browser package path')
            seen.add(str(relative)); total += member.size
            if total > 32 * 1024 * 1024 or not (member.isfile() or member.isdir()):
                raise ValueError('Browser archive bounds/type')
            target = destination / str(relative)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as stream:
                    data = stream.read(member.size + 1)
                if len(data) != member.size:
                    raise ValueError('Incomplete browser package')
                write_file(target, data)


def receive(stream, root):
    """Finite framed files; no archive paths, expansion or host report execution."""
    header = stream.readline(65537)
    if len(header) > 65536 or not header.endswith(b'\n'):
        raise ValueError('Browser artifact metadata limit/incomplete frame')
    from .documents import decode
    result = decode(header)
    files = result.get('files')
    if not isinstance(files, list) or len(files) > 10:
        raise ValueError('Browser artifact file count')
    names, total, pngs = set(), 0, 0
    inventory = {}
    root.mkdir()
    for item in files:
        if not isinstance(item, dict) or set(item) != {'name', 'size', 'sha256'}:
            raise ValueError('Browser artifact metadata shape')
        name, size = item['name'], item['size']
        if not isinstance(name, str) or name in names or type(size) is not int or size < 1 or not isinstance(item['sha256'], str) or not HEX.fullmatch(item['sha256']):
            raise ValueError('Invalid browser artifact identity')
        names.add(name)
        if re.fullmatch(r'screen-[1-8]\.png', name):
            cap = 2 * 1024 * 1024; pngs += 1
        elif name == 'trace.zip':
            cap = 16 * 1024 * 1024
        elif name == 'events.json':
            cap = 256 * 1024
        else:
            raise ValueError('Unexpected browser artifact filename')
        total += size
        if size > cap or total > LIMIT:
            raise ValueError('Browser artifact byte limit')
        data = stream.read(size)
        if len(data) != size or digest(data) != item['sha256']:
            raise ValueError('Incomplete/corrupt browser artifact')
        if name.endswith('.png') and (len(data) < 24 or data[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' or struct.unpack('>II',data[16:24]) != (1280,800)):
            raise ValueError('Browser screenshot must be viewport PNG1280x800')
        if name == 'trace.zip' and not data.startswith(b'PK\x03\x04'):
            raise ValueError('Browser trace must be opaque ZIP')
        if name == 'events.json':
            events = decode(data)
            if not isinstance(events, list) or len(events) > 512:
                raise ValueError('Browser event count limit')
        write_file(root / name, data)
        inventory[name] = {'size': size, 'sha256': item['sha256']}
    if stream.read(1):
        raise ValueError('Trailing browser artifact bytes')
    if result.get('status') == 'passed' and (pngs < 1 or not {'trace.zip','events.json'} <= names):
        raise ValueError('Passing browser check requires complete screenshot/trace/events')
    if result.get('status') not in ('passed', 'failed'):
        raise ValueError('Invalid browser outcome')
    return result, inventory


class BrowserStore:
    """Private browser evidence and support with one exclusive operation lease."""
    def __init__(self, root, *, executor=None):
        self.root=Path(root).absolute()
        if any(p.is_symlink() for p in (self.root,*self.root.parents)):
            raise ValueError('Browser store cannot use symlinks')
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        info=self.root.stat()
        if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
            raise ValueError('Browser store must be controller-owned mode0700')
        self.label=digest(str(self.root).encode())
        from .browser_pair import run
        self.pair = executor or run

    @contextmanager
    def locked(self, shared=False):
        fd=os.open(self.root/'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'a') as lock:
            if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):
                raise ValueError('Invalid browser store lease')
            try:fcntl.flock(lock,(fcntl.LOCK_SH if shared else fcntl.LOCK_EX)|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('Another browser operation owns this store') from None
            yield

    def _reserve(self):
        count = total = 0
        for path in self.root.iterdir():
            if path.name == '.lock': continue
            if path.name.startswith('.'):
                raise ValueError('Browser recovery required before reuse')
            receipt = self._inspect(path.name)
            count += receipt['receipt']['kind'] == 'result'
            total += sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
        if count >= 16 or total + 64*1024*1024 > 512*1024*1024:
            raise ValueError('Browser store full; no implicit eviction')

    def prepare(self, archives):
        with self.locked():
            self._reserve()
            images=installed_images()
            stage = Path(tempfile.mkdtemp(prefix='.stage-',dir=self.root))
            try:
                support = stage/'support';support.mkdir()
                for name, expected in PACKAGES.items():
                    support_archive(Path(archives)/(name+'.tgz'),support/name,expected)
                freeze(support)
                receipt = {'kind':'support','created_utc':utc(),'packages':PACKAGES,'installed_images':images,
                           'tree_sha256':tree_hash(support),'image':BROWSER_IMAGE,'app_image':NODE_IMAGE,
                           'seccomp_sha256':SECCOMP}
                result = self._commit(stage,receipt);stage=None
                return result
            finally:
                if stage is not None:discard(stage)

    def _commit(self,stage,receipt, *, cancelled=lambda:False):
        raw=encoded(receipt)
        if len(raw)>65536:raise ValueError('Browser receipt limit')
        identifier=digest(raw);write_file(stage/'receipt.json',raw)
        result=self._inspect(identifier,staging=stage)
        sync_directory(stage)
        if os.path.lexists(self.root/identifier):raise ValueError('Browser receipt already exists')
        active(cancelled)
        stage.rename(self.root/identifier)
        return result

    def _inspect(self,identifier,staging=None):
        if not isinstance(identifier,str) or not HEX.fullmatch(identifier):raise ValueError('Invalid browser receipt ID')
        root=self.root/identifier if staging is None else staging
        info=root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:raise ValueError('Browser record type/ownership')
        raw=checked_file(root/'receipt.json',65536)
        if digest(raw)!=identifier:raise ValueError('Browser receipt hash mismatch')
        receipt=json.loads(raw)
        if receipt['kind']=='support':
            if {p.name for p in root.iterdir()}!={'receipt.json','support'} or tree_hash(root/'support')!=receipt['tree_sha256']:raise ValueError('Browser support changed')
            if receipt['packages']!=PACKAGES or receipt['image']!=BROWSER_IMAGE or receipt['app_image']!=NODE_IMAGE or receipt['seccomp_sha256']!=SECCOMP:raise ValueError('Unsupported browser support recipe')
        elif receipt['kind']=='result':
            if {p.name for p in root.iterdir()}!={'receipt.json','app','checks','seed.json','artifacts'}:raise ValueError('Unexpected browser result entries')
            for name,entries,size in [('app',256,4*1024*1024),('checks',64,1024*1024)]:
                if tree_hash(root/name,ArchiveLimits(entries=entries,expanded_bytes=size))!=receipt['inputs'][name]:raise ValueError('Browser frozen input changed')
            if digest(checked_file(root/'seed.json',65536))!=receipt['inputs']['seed']:raise ValueError('Browser seed changed')
            artifact_info=(root/'artifacts').lstat()
            if not stat.S_ISDIR(artifact_info.st_mode) or artifact_info.st_uid!=os.getuid():raise ValueError('Browser artifact directory changed')
            files=receipt['artifacts']
            if {p.name for p in (root/'artifacts').iterdir()}!=set(files):raise ValueError('Browser artifacts changed')
            for name,facts in files.items():
                if not re.fullmatch(r'screen-[1-8]\.png|trace\.zip|events\.json',name):raise ValueError('Invalid artifact path')
                raw=checked_file(root/'artifacts'/name,LIMIT)
                if len(raw)!=facts['size'] or digest(raw)!=facts['sha256']:raise ValueError('Browser artifact hash mismatch')
        elif receipt['kind']=='recovery':
            if {p.name for p in root.iterdir()}!={'receipt.json'}:raise ValueError('Unexpected recovery receipt files')
        else:raise ValueError('Unknown browser receipt kind')
        return {'id':identifier,'receipt':receipt}

    def inspect(self,identifier):
        with self.locked(shared=True):return self._inspect(identifier)

    def check(self, approved, *, cancelled=lambda:False):
        required={'app','checks','seed','case','support'}
        if not isinstance(approved,dict) or set(approved)!=required or not isinstance(approved['case'],str) or not re.fullmatch('[a-zA-Z0-9_-]{1,64}',approved['case']):
            raise ValueError('Browser approval requires app/checks/seed/case/support only')
        approved=json.loads(encoded(approved))
        with self.locked():
            self._reserve();active(cancelled)
            support=self._inspect(approved['support'])
            if support['receipt']['kind']!='support':raise ValueError('Browser requires prepared support')
            if digest((RECIPE/'seccomp.json').read_bytes())!=SECCOMP:raise ValueError('Browser seccomp profile changed')
            stage=Path(tempfile.mkdtemp(prefix='.stage-',dir=self.root));work=None
            try:
                inputs={'app':snapshot(approved['app'],stage/'app',256,4*1024*1024),
                        'checks':snapshot(approved['checks'],stage/'checks',64,1024*1024)}
                if not (stage/'app'/'server.cjs').is_file() or not (stage/'checks'/'journey.cjs').is_file():raise ValueError('Fixed app/check entry missing')
                seed=Path(approved['seed'])
                if any(p.is_symlink() for p in (seed,*seed.absolute().parents)) or not seed.is_file() or seed.stat().st_size>65536:raise ValueError('Invalid seed input')
                before=seed.stat()
                with seed.open('rb') as stream:data=stream.read(65537)
                if seed.stat()!=before or len(data)>65536:raise ValueError('Seed changed during copy')
                json.loads(data);write_file(stage/'seed.json',data);inputs['seed']=digest(data)
                work=Path(tempfile.mkdtemp(prefix='.work-',dir=self.root))
                import uuid
                run=uuid.uuid4().hex
                app_name='gflo-browser-app-'+run;browser_name='gflo-browser-check-'+run
                def command(name,image,network,memory,cpus,pids,shm,tmp):
                    return ['docker','run','--rm','--pull','never','--name',name,'--label','gflo.browser='+self.label,
                            '--label','gflo.browser.run='+run,'--log-driver','none','--runtime','runc','--network',network,'--read-only',
                            '--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges',
                            '--memory',memory,'--memory-swap',memory,'--cpus',cpus,'--pids-limit',pids,
                            '--ipc','private','--shm-size',shm,'--init','--tmpfs','/tmp:rw,nosuid,nodev,size='+tmp+',mode=1777',
                            '--env','HOME=/tmp']
                def mount(args,source,target):args.extend(['--mount',f'type=bind,src={source},dst={target},readonly'])
                app=command(app_name,NODE_IMAGE,'none','128m','.25','64','16m','16m')
                mount(app,stage/'app','/app');mount(app,stage/'seed.json','/seed.json')
                app+=['--env','GFLO_SEED_FILE=/seed.json','--workdir','/app',NODE_IMAGE,'node','server.cjs']
                browser=command(browser_name,BROWSER_IMAGE,'OWNED_APP','1g','2','256','256m','256m')
                browser+=['--security-opt','seccomp='+str(RECIPE/'seccomp.json')]
                mount(browser,self.root/approved['support']/'support','/support');mount(browser,stage/'checks','/checks')
                mount(browser,RECIPE/'journey.cjs','/journey.cjs')
                browser+=['--env','NODE_PATH=/support','--workdir','/tmp',BROWSER_IMAGE,'node','/journey.cjs']
                spec={'app_image':NODE_IMAGE,'browser_image':BROWSER_IMAGE,'run':run,'app_name':app_name,'browser_name':browser_name,'app_args':app,'browser_args':browser,'facts':str(work/'facts.json')}
                marker=self.root/'.cleanup-required';write_file(marker,encoded({'run':run,'names':[browser_name,app_name]}))
                active(cancelled)
                with tempfile.TemporaryFile(dir=work) as transport:
                    try:
                        outcome=self.pair(spec,transport,cancelled=cancelled)
                    except BaseException as error:
                        write_file(self.root/'.failure.json',encoded({'case':approved['case'],'diagnostics':str(error)[:4096],'cleanup':{'confirmed':False,'uncertain_creates':[app_name,browser_name]}}))
                        raise
                    facts=outcome['facts'];confirmed=facts.get('cleanup',{}).get('confirmed') is True
                    if confirmed:marker.unlink()
                    transport.seek(0)
                    try:result,artifacts=receive(transport,stage/'artifacts')
                    except (ValueError,OSError) as error:
                        if (stage/'artifacts').exists():shutil.rmtree(stage/'artifacts')
                        (stage/'artifacts').mkdir();artifacts={}
                        result={'status':'failed','failure':{'phase':'artifact','message':str(error)[:4096]}}
                if outcome['exit_code'] or outcome['reason'] or outcome.get('transport_errors') or not confirmed or facts.get('failure'):
                    result['status']='failed';result['executor_failure']=outcome['reason'] or facts.get('failure') or outcome['exit_code']
                if not confirmed:
                    write_file(self.root/'.failure.json',encoded({'case':approved['case'],'diagnostics':outcome['diagnostics'][-4096:],'cleanup':facts.get('cleanup')}))
                    raise RuntimeError('Browser cleanup uncertain; failed diagnostics retained, explicit recovery required')
                receipt={'kind':'result','created_utc':utc(),'approved':approved,'inputs':inputs,'support':support['id'],
                         'helpers':{name:digest((RECIPE/name).read_bytes()) for name in ['journey.cjs','seccomp.json']},
                         'outcome':result,'executor':outcome,'artifacts':artifacts}
                shutil.rmtree(work);work=None
                # Cancellation is saved as a failed result when cleanup and capture are complete.
                if cancelled():receipt['outcome']['status']='failed';receipt['outcome']['executor_failure']='cancelled'
                published=self._commit(stage,receipt,cancelled=cancelled);stage=None
                return published
            finally:
                if work is not None:shutil.rmtree(work)
                if stage is not None:discard(stage)

    def cleanup(self, *, acknowledge_create_uncertainty=False):
        with self.locked():
            evidence={};uncertain=[]
            for name in ['.failure.json','.cleanup-required']:
                path=self.root/name
                if path.exists():
                    raw=checked_file(path,65536)
                    evidence[name]={'sha256':digest(raw),'value':json.loads(raw)}
                    uncertain.extend(evidence[name]['value'].get('cleanup',{}).get('uncertain_creates',[]))
            for path in self.root.glob('.work-*'):
                if path.is_symlink() or not path.is_dir():raise ValueError('Invalid browser recovery work directory')
                facts=path/'facts.json'
                if not facts.exists():
                    uncertain.append('guardian completion not recorded')
                else:
                    raw=checked_file(facts,65536,0o644)
                    value=json.loads(raw)
                    if len(evidence)>=8:raise ValueError('Recovery evidence count limit')
                    evidence[path.name+'/facts.json']={'sha256':digest(raw),'value':value}
                    uncertain.extend(value.get('cleanup',{}).get('uncertain_creates',[]))
            uncertain=sorted(set(uncertain))
            result=subprocess.run(['docker','ps','-aq','--no-trunc','--filter','label=gflo.browser='+self.label],capture_output=True,text=True,check=True,timeout=15)
            ids=result.stdout.split()
            if ids:
                # Browser first; labels and inspect establish this store's ownership.
                facts=json.loads(subprocess.run(['docker','inspect',*ids],capture_output=True,text=True,check=True,timeout=15).stdout)
                facts.sort(key=lambda f:0 if f['Name'].startswith('/gflo-browser-check-') else 1)
                for fact in facts:
                    if fact['Config']['Labels'].get('gflo.browser')!=self.label:raise ValueError('Recovery ownership changed')
                    subprocess.run(['docker','rm','-f',fact['Id']],capture_output=True,check=True,timeout=30)
            remaining=subprocess.run(['docker','ps','-aq','--filter','label=gflo.browser='+self.label],capture_output=True,text=True,check=True,timeout=15)
            if remaining.stdout.strip():raise ValueError('Browser cleanup incomplete')
            if uncertain and not acknowledge_create_uncertainty:
                raise ValueError('Create completion remains uncertain despite current absence; verify the daemon has settled, then cleanup with --acknowledge-create-uncertainty')
            if evidence:
                # This immutable record attests the operator acknowledgement and
                # current readback, not successful completion of uncertain creates.
                receipt={'kind':'recovery','created_utc':utc(),'operator_acknowledged_create_uncertainty':bool(uncertain and acknowledge_create_uncertainty),
                         'uncertain_creates':uncertain,'original_failure_evidence':evidence,
                         'daemon_readback':'currently absent; not proof of create completion'}
                stage=Path(tempfile.mkdtemp(prefix='.stage-',dir=self.root))
                try:
                    self._commit(stage,receipt);stage=None
                finally:
                    if stage is not None:discard(stage)
            for path in self.root.iterdir():
                if path.name.startswith(('.stage-','.work-')):discard(path)
            for name in ['.failure.json','.cleanup-required']:
                marker=self.root/name
                if marker.exists():checked_file(marker,65536);marker.unlink()
