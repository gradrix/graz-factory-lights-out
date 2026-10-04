"""Read-only final publication download; validates every local artifact hash."""
import argparse,hashlib,json,subprocess
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--stage',required=True);a=parser.parse_args()
p=Path(__file__).resolve().parent;local=Path('.gflo/executable-review-protocol-trial-1');local.mkdir(exist_ok=True)
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','monster-gaming-pc.lan'];remote=a.stage+'/trial-1/'
for name in ['artifact-hashes.json','experiment.json','results.json']:
 raw=subprocess.check_output(ssh+['cat',remote+name],timeout=20)
 with(local/name).open('xb')as out:out.write(raw)
 (p/('trial-'+name)).write_bytes(raw)
man=json.loads((local/'artifact-hashes.json').read_bytes())
for name,digest in man.items():
 q=Path(name);assert not q.is_absolute() and '..' not in q.parts
 assert hashlib.sha256((local/q).read_bytes()).hexdigest()==digest,name
actual={str(x.relative_to(local))for x in local.rglob('*')if x.is_file()}
assert actual==set(man)|{'artifact-hashes.json'}
receipt={'verified_entries':len(man),'manifest_sha256':hashlib.sha256((local/'artifact-hashes.json').read_bytes()).hexdigest(),'exact_file_set':True}
(p/'trial-download-integrity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
