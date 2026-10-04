"""Copy completed trial artifacts without executing candidate code."""
import hashlib, io, json, os, subprocess, tarfile
from pathlib import Path, PurePosixPath

stage = '/home/gradrix/gflo-planning-d186b93'
evidence = Path(__file__).resolve().parent
root = Path('.gflo/planning-trial-1')
ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'monster-gaming-pc.lan']
monitor = subprocess.check_output(ssh + ['python3', '-'], input=(evidence/'monitor-trial.py').read_bytes(), timeout=20)
state = json.loads(monitor)
assert not state['controller_alive'] and state['artifact_manifest_present'], state
assert len(state['arms']) == 4 and all(a.get('cleanup') and a.get('idle') for a in state['arms']), state
(evidence/'trial-final-monitor.json').write_bytes(monitor)
arm = '4-config-preview-direct'
assert not (root/arm).exists()
raw = subprocess.check_output(ssh + ['tar', '-cf', '-', '-C', stage+'/trial-1', arm], timeout=40)
assert len(raw) < 256*1024*1024
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
    entries = archive.getmembers()
    assert len(entries) < 20000
    for item in entries:
        parts = PurePosixPath(item.name).parts
        assert parts and parts[0] == arm and '..' not in parts and not item.name.startswith('/')
        assert item.isdir() or item.isfile()
    for item in entries:
        path = root/item.name
        if item.isdir(): path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as out: out.write(archive.extractfile(item).read())
        os.chmod(path, item.mode & 0o777)
receipt = {'arm':arm, 'archive_bytes':len(raw), 'archive_sha256':hashlib.sha256(raw).hexdigest(),
           'local_copy':str(root/arm), 'result':json.loads((root/arm/'result.json').read_bytes())}
(evidence/'arm-4-download.json').write_text(json.dumps(receipt,indent=2)+'\n')
for name in ['results.json','artifact-hashes.json']:
    data = subprocess.check_output(ssh + ['cat',stage+'/trial-1/'+name], timeout=20)
    (root/name).write_bytes(data)
    (evidence/('trial-'+name)).write_bytes(data)
manifest=json.loads((root/'artifact-hashes.json').read_bytes())
verified=[]; absent=[]
for name,digest in manifest.items():
    path=PurePosixPath(name)
    assert not path.is_absolute() and '..' not in path.parts
    local=root/name
    if not local.exists(): absent.append(name); continue
    assert hashlib.sha256(local.read_bytes()).hexdigest()==digest, name
    verified.append(name)
# Root metadata may include additional frozen receipts, copy individually after path validation.
for name in absent:
    assert len(PurePosixPath(name).parts)==1, name
    data=subprocess.check_output(ssh+['cat',stage+'/trial-1/'+name],timeout=20)
    assert hashlib.sha256(data).hexdigest()==manifest[name]
    (root/name).write_bytes(data); verified.append(name)
report={'verified_file_count':len(verified),'all_manifest_entries_match':len(verified)==len(manifest),
        'manifest_sha256':hashlib.sha256((root/'artifact-hashes.json').read_bytes()).hexdigest(),
        'raw_local_root':str(root),'rig_root':stage+'/trial-1','no_candidate_execution':True}
(evidence/'trial-download-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'result':receipt['result'],'integrity':report},indent=2))
