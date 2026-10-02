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

# Reconstruct only trusted files from the exact reviewed repository commit.
# Local duplicate source/corpus trees alongside this script are never imported.
ROOT = Path(__file__).resolve().parent
CANDIDATE = '0c9c7c8fffdc6d16f316a3650cd28a78ab265095'
REPO = Path(subprocess.check_output(
    ['git', '-C', str(ROOT), 'rev-parse', '--show-toplevel'], text=True).strip())
FROZEN = REPO / '.gflo' / 'security-artifact' / CANDIDATE
files = subprocess.check_output([
    'git', '-C', str(REPO), 'ls-tree', '-r', '--name-only', CANDIDATE,
    'gflo/__init__.py', 'gflo/artifacts.py', 'tests/test_environment_artifacts.py',
    'evaluations/environment-artifacts'], text=True).splitlines()
for relative in files:
    target = FROZEN / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(subprocess.check_output(
        ['git', '-C', str(REPO), 'show', f'{CANDIDATE}:{relative}']))
sys.path.insert(0, str(FROZEN))
from gflo.artifacts import ArchiveLimits, unpack_archive

RESULTS = []
def record(name, fn):
    try:
        detail = fn()
        RESULTS.append({'probe': name, 'status': 'pass', 'detail': detail})
    except Exception as error:
        RESULTS.append({'probe': name, 'status': 'fail', 'error': repr(error)})

# Hand-encoded USTAR headers, independent of tarfile's serializer.
def header(name=b'file', size=0, kind=b'0', mode=0o644, prefix=b'', overrides=()):
    raw = bytearray(512)
    for start, length, data in [(0,100,name), (100,8,f'{mode:07o}\0'.encode()),
        (108,8,b'0000000\0'), (116,8,b'0000000\0'),
        (124,12,f'{size:011o}\0'.encode()), (136,12,b'00000000000\0'),
        (156,1,kind), (257,8,b'ustar\x0000'), (345,155,prefix)]:
        assert len(data) <= length
        raw[start:start+len(data)] = data
    for start, data in overrides:
        raw[start:start+len(data)] = data
    raw[148:156] = b'        '
    raw[148:156] = f'{sum(raw):06o}\0 '.encode()
    return bytes(raw)

def archive(name=b'file', data=b'abc', **kwargs):
    return header(name, len(data), **kwargs) + data + bytes(-len(data)%512) + bytes(1024)

class Watched(io.BytesIO):
    def __init__(self, data, destination, fragment=0):
        super().__init__(data)
        self.destination = destination
        self.fragment = fragment
        self.calls = 0
        self.requests = []
    def read(self, size):
        assert not self.destination.exists(), 'extraction began before complete validation'
        self.calls += 1
        self.requests.append(size)
        return super().read(min(size, self.fragment) if self.fragment else size)

def reject(data, limits=ArchiveLimits(), fragment=0):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        keep = root / 'keep'
        keep.write_bytes(b'unchanged')
        dest = root / 'new'
        stream = Watched(data, dest, fragment)
        try:
            unpack_archive(stream, dest, limits)
        except ValueError as error:
            assert not os.path.lexists(dest)
            assert keep.read_bytes() == b'unchanged'
            assert sorted(p.name for p in root.iterdir()) == ['keep']
            return {'error': str(error), 'bytes_read': stream.tell(), 'read_calls': stream.calls}
        raise AssertionError('unexpected acceptance')

def accept(data, limits=ArchiveLimits(), fragment=0):
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / 'new'
        stream = Watched(data, dest, fragment)
        unpack_archive(stream, dest, limits)
        paths = list(dest.rglob('*'))
        assert stat.S_IMODE(dest.stat().st_mode) == 0o700
        assert not any(p.is_symlink() for p in paths)
        return {'nodes': len(paths), 'files': {str(p.relative_to(dest)): {'bytes':p.read_bytes().hex(), 'mode':oct(stat.S_IMODE(p.stat().st_mode))} for p in paths if p.is_file()}, 'bytes_read':stream.tell()}

manifest = json.loads((FROZEN/'evaluations/environment-artifacts/manifest.json').read_text())
for case in manifest['archive_cases']:
    def run(case=case):
        data = (FROZEN/'evaluations/environment-artifacts'/case['archive']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == case['sha256']
        return (accept if case['expected_result']=='accept' else reject)(data, ArchiveLimits(**case['bounds']))
    record('corpus/'+case['id'], run)

for name, data in {
    'invalid-checksum':bytes([archive()[0]^1])+archive()[1:],
    'invalid-utf8':archive(b'\xff'),
    'invalid-octal-size':header(overrides=[(124,b'not-an-octal!')])+bytes(1024),
    'negative-base256-size':header(overrides=[(124,bytes([255])*12)])+bytes(1024),
    'huge-base256-size':header(overrides=[(124,bytes([128])+((1<<70).to_bytes(11,'big')))]),
    'ustar-version':header(overrides=[(263,b'01')])+bytes(1024),
    'pax-global':header(kind=b'g')+bytes(1024),
    'unknown-type':header(kind=b'Z')+bytes(1024),
    'prefix-traversal':archive(b'file',prefix=b'../../escape'),
    'prefix-absolute':archive(b'file',prefix=b'/tmp'),
    'backslash-path':archive(b'a\\b'),
    'noncanonical-dot':archive(b'a/./b'),
    'directory-with-body':archive(b'dir/', kind=b'5'),
    'nonzero-file-padding':header(size=1)+b'a'+b'x'+bytes(510)+bytes(1024),
    'single-zero-trailer':header()+bytes(512),
    'nonzero-second-trailer':header()+bytes(512)+header(),
    'trailing-data':archive()+b'evil',
    'concatenated-archives':archive()+archive(b'later'),
    'truncated-final-trailer':archive()[:-1],
}.items():
    record(name, lambda data=data:reject(data))

record('fragmented-one-byte-valid-control', lambda:accept(archive(b'bin/check',b'pass',mode=0o6755),fragment=1))
record('mode-normalization', lambda:accept(archive(b'file',mode=0o666)))
record('exact-all-caps-control',lambda:accept(archive(b'file',b'abc'),ArchiveLimits(transport_bytes=2048,entries=1,expanded_bytes=3,path_bytes=4)))
record('transport-one-byte-over',lambda:reject(archive()+b'\0',ArchiveLimits(transport_bytes=2048)))
record('path-one-byte-over',lambda:reject(archive(b'files'),ArchiveLimits(path_bytes=4)))
record('multibyte-path-over',lambda:reject(archive('ééé'.encode()),ArchiveLimits(path_bytes=5)))
record('transport-cap-during-header',lambda:reject(archive(),ArchiveLimits(transport_bytes=1)))

def declared_early():
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)/'new'
        class OnlyHeader:
            calls = 0
            def read(self, size):
                self.calls += 1
                assert self.calls == 1, 'requested declared body'
                return header(size=134217729)
        stream=OnlyHeader()
        try:
            unpack_archive(stream,dest)
        except ValueError as error:
            assert 'expanded-byte' in str(error)
            assert stream.calls == 1
            assert not dest.exists()
            return {'read_calls':stream.calls,'error':str(error)}
        raise AssertionError('unexpected acceptance')
record('instrumented-declared-size-no-body-read',declared_early)

for kind in ['file','directory','symlink','dangling-symlink','ancestor-symlink']:
    def protected(kind=kind):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            outside=root/'outside'
            outside.mkdir()
            (outside/'keep').write_text('unchanged')
            dest=root/'target'
            if kind=='file': dest.write_text('unchanged')
            elif kind=='directory':
                dest.mkdir()
                (dest/'keep').write_text('unchanged')
            elif kind=='symlink':dest.symlink_to(outside,target_is_directory=True)
            elif kind=='dangling-symlink':dest.symlink_to(root/'absent')
            else:
                (root/'link').symlink_to(outside,target_is_directory=True)
                dest=root/'link'/'target'
            class Unreadable:
                def read(self,size):raise AssertionError('read before protecting destination')
            try:unpack_archive(Unreadable(),dest)
            except ValueError as error:
                assert (outside/'keep').read_text()=='unchanged'
                if kind=='file':assert dest.read_text()=='unchanged'
                if kind=='directory':assert (dest/'keep').read_text()=='unchanged'
                if kind in ['symlink','dangling-symlink']:assert dest.is_symlink()
                if kind=='ancestor-symlink':assert not (outside/'target').exists()
                return str(error)
            raise AssertionError('unexpected acceptance')
    record('destination-'+kind,protected)

def cleanup():
    with tempfile.TemporaryDirectory() as tmp:
        dest=Path(tmp)/'new'
        with patch('gflo.artifacts.os.fsync',side_effect=OSError('controlled fsync failure')):
            try:unpack_archive(io.BytesIO(archive()),dest)
            except OSError as error:
                assert not dest.exists()
                return str(error)
        raise AssertionError('failure was not reached')
record('failed-extraction-removes-staging',cleanup)

def directory_amplification():
    name='/'.join(['r00000']+['a']*110+['f']).encode()
    split=name.rfind(b'/',0,150)
    detail=reject(archive(name=name[split+1:],data=b'',prefix=name[:split]),ArchiveLimits(entries=1))
    assert 'filesystem entry' in detail['error']
    assert detail['bytes_read']==512
    detail['configured_entries']=1
    detail['path_bytes']=len(name)
    detail['observation']='formerly accepted 112-node tree now rejected after header before extraction'
    return detail
record('filesystem-node-amplification',directory_amplification)


def nodes_control():
    data=archive(b'a/x', b'x')[:-1024]+archive(b'a/y', b'y')[:-1024]+header(b'a/', kind=b'5')+bytes(1024)
    detail=accept(data,ArchiveLimits(entries=3))
    assert detail['nodes']==3
    assert detail['files']['a/x']['bytes']=='78'
    assert detail['files']['a/y']['bytes']=='79'
    return detail
record('shared-parent-late-explicit-directory-at-cap',nodes_control)
record('implicit-parent-exact-node-cap',lambda:accept(archive(b'a/b/c',b'x'),ArchiveLimits(entries=3)))
record('implicit-parent-one-node-over',lambda:reject(archive(b'a/b/c',b'x'),ArchiveLimits(entries=2)))
record('late-path-union-over-cap',lambda:reject(archive(b'a/b',b'x')[:-1024]+archive(b'c/d',b'y'),ArchiveLimits(entries=3)))

def no_body_for_nodes():
    with tempfile.TemporaryDirectory() as tmp:
        dest=Path(tmp)/'new'
        class OneHeader:
            calls=0
            def read(self,size):
                self.calls+=1
                assert self.calls==1,'attempted body read after node limit violation'
                return header(b'a/b/c',size=100)
        stream=OneHeader()
        try:unpack_archive(stream,dest,ArchiveLimits(entries=2))
        except ValueError as error:
            assert 'filesystem entry' in str(error)
            assert stream.calls==1
            assert not dest.exists()
            return {'read_calls':stream.calls,'error':str(error)}
        raise AssertionError('unexpected acceptance')
record('node-limit-rejects-before-body-read',no_body_for_nodes)

result={'candidate':'0c9c7c8fffdc6d16f316a3650cd28a78ab265095','python':platform.python_version(),'source_sha256':hashlib.sha256((FROZEN/'gflo/artifacts.py').read_bytes()).hexdigest(),'pass':sum(r['status']=='pass' for r in RESULTS),'fail':sum(r['status']=='fail' for r in RESULTS),'results':RESULTS}
(FROZEN/'rerun-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
for r in RESULTS:
    if r['status']=='fail' or r['probe']=='filesystem-node-amplification':print(json.dumps(r))

print(f'Rerun evidence: {FROZEN / "rerun-results.json"}', flush=True)
subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_environment_artifacts.py', '-v'], cwd=FROZEN, check=True)
sys.exit(1 if result['fail'] else 0)
