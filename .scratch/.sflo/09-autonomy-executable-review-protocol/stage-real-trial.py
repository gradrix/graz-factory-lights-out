"""Stage hash-bound code and public fixtures only; performs no inference."""
from pathlib import Path, PurePosixPath
import argparse,hashlib,io,json,shlex,stat,subprocess,tarfile
parser=argparse.ArgumentParser();parser.add_argument("--synthetic",action="store_true");args=parser.parse_args()

repo=Path('/home/gradrix/repos/gflo-review-protocol-prototype')
evidence=Path(__file__).resolve().parent
prior=evidence.parent/'08-autonomy-planning-pilot'
stage='/home/gradrix/gflo-review-protocol-'+json.loads((evidence/'builder-candidate.json').read_bytes())['prototype_commit'][:7]
if args.synthetic:stage+='-controls'
receipt_prefix='synthetic-' if args.synthetic else ''
freeze=json.loads((evidence/'builder-candidate.json').read_bytes())
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip()==freeze['prototype_commit']
entries={}
for name,digest in {**freeze['reused_source_sha256'],'ops/executable_review_prototype.py':freeze['source_sha256']['ops/executable_review_prototype.py']}.items():
 p=repo/name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest,name
 entries[name]=(raw,stat.S_IMODE(p.stat().st_mode))
if args.synthetic:
 name='ops/executable_review_vertical_qa.py';p=repo/name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==freeze['source_sha256'][name];entries[name]=(raw,stat.S_IMODE(p.stat().st_mode))
fixture=repo/'evaluations/executable-review'
manifest=json.loads((fixture/'manifest.json').read_bytes())
assert hashlib.sha256((fixture/'manifest.json').read_bytes()).hexdigest()=='05de766048d96216865b8e5d0c817166ac1635391a6ed496b9ce6c3b0b6bdb37'
for name,digest in manifest['files'].items():
 assert name.startswith('public/')
 p=fixture/name;assert not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
 assert stat.S_IMODE(p.stat().st_mode)==manifest['modes'][name]
 entries['evaluations/executable-review/'+name]=(p.read_bytes(),manifest['modes'][name])
entries['evaluations/executable-review/manifest.json']=((fixture/'manifest.json').read_bytes(),0o644)
for name,p in [('inputs/contract.md',evidence/'contract.md'),('inputs/environment-bindings.json',prior/'environment-bindings.json'),('inputs/expected-identity.json',prior/'serving-lifecycle/expected-identity.json')]:entries[name]=(p.read_bytes(),0o644)
directories={}
for name in entries:
 for parent in PurePosixPath(name).parents:
  if str(parent)=='.':continue
  local=repo/str(parent)
  directories[str(parent)]=stat.S_IMODE(local.stat().st_mode) if local.is_dir() else 0o755
inventory={'prototype_commit':freeze['prototype_commit'],'files':{name:{'sha256':hashlib.sha256(raw).hexdigest(),'mode':mode}for name,(raw,mode)in entries.items()},'directories':directories,'excluded':['private expectations','reference solutions','tests',*(() if args.synthetic else ('synthetic transport drivers',)),'private model config/key']}
entries['inventory.json']=(json.dumps(inventory,indent=2).encode()+b'\n',0o644)
stream=io.BytesIO()
with tarfile.open(fileobj=stream,mode='w') as archive:
 for name,mode in sorted(directories.items(),key=lambda x:(x[0].count('/'),x[0])):
  info=tarfile.TarInfo(name);info.type=tarfile.DIRTYPE;info.mode=mode;archive.addfile(info)
 for name,(raw,mode)in entries.items():
  info=tarfile.TarInfo(name);info.size=len(raw);info.mode=mode;archive.addfile(info,io.BytesIO(raw))
raw=stream.getvalue();assert len(raw)<5*1024*1024
remote='''import hashlib,io,json,os,pathlib,stat,sys,tarfile
root=pathlib.Path(STAGE);root.mkdir(mode=0o700)
raw=sys.stdin.buffer.read(5*1024*1024+1);assert len(raw)<=5*1024*1024
with tarfile.open(fileobj=io.BytesIO(raw))as a:
 for item in a.getmembers():
  p=pathlib.PurePosixPath(item.name);assert not p.is_absolute()and '..'not in p.parts and(item.isdir()or item.isfile())
  dest=root/item.name
  if item.isdir():dest.mkdir(parents=True,exist_ok=True)
  else:
   dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open('xb')as out:out.write(a.extractfile(item).read())
  os.chmod(dest,item.mode&0o777)
inventory=json.loads((root/'inventory.json').read_bytes())
for name,facts in inventory['files'].items():
 p=root/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==facts['sha256']and stat.S_IMODE(p.stat().st_mode)==facts['mode'],name
for name,mode in inventory['directories'].items():assert stat.S_IMODE((root/name).stat().st_mode)==mode,name
sys.path[:0]=[str(root/'ops'),str(root)]
import executable_review_prototype as p
m=root/'evaluations/executable-review/manifest.json';p.verify_manifest(m,'05de766048d96216865b8e5d0c817166ac1635391a6ed496b9ce6c3b0b6bdb37')
bindings=json.loads((root/'inputs/environment-bindings.json').read_bytes())
environment=p.resolve_binding(bindings['python-stdlib']);assert environment.runtime['python']=='3.12.13'
result={'stage':str(root),'files_verified':len(inventory['files']),'directories_verified':len(inventory['directories']),'inventory_sha256':hashlib.sha256((root/'inventory.json').read_bytes()).hexdigest(),'manifest_verified':True,'environment_id':environment.id,'no_inference':True}
(root/'staging-validation.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result))
'''.replace('STAGE',repr(stage))
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','monster-gaming-pc.lan','python3 -c '+shlex.quote(remote)],input=raw,capture_output=True,timeout=60)
(evidence/(receipt_prefix+'staging-command-result.json')).write_text(json.dumps({'exit':result.returncode,'stdout':result.stdout.decode(),'stderr':result.stderr.decode()},indent=2)+'\n')
result.check_returncode();facts=json.loads(result.stdout)
(evidence/(receipt_prefix+'staging.json')).write_text(json.dumps({'archive_sha256':hashlib.sha256(raw).hexdigest(),'archive_bytes':len(raw),'inventory':inventory,'validation':facts},indent=2)+'\n')
print(json.dumps(facts,indent=2))
