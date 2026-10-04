"""Copy a completed review case read-only; never execute its candidate."""
import argparse,hashlib,io,json,os,subprocess,tarfile
from pathlib import Path,PurePosixPath
parser=argparse.ArgumentParser();parser.add_argument('case',choices=['case-01','case-02','case-03','case-04']);parser.add_argument('--stage',required=True);args=parser.parse_args()
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','monster-gaming-pc.lan'];stage=args.stage+'/trial-1'
result=json.loads(subprocess.check_output(ssh+['cat',stage+'/'+args.case+'/result.json'],timeout=15));assert result['cleanup_confirmed']and result['idle_confirmed']
root=Path('.gflo/executable-review-protocol-trial-1');assert not(root/args.case).exists()
raw=subprocess.check_output(ssh+['tar','-cf','-','-C',stage,args.case],timeout=30);assert len(raw)<32*1024*1024
with tarfile.open(fileobj=io.BytesIO(raw))as archive:
 entries=archive.getmembers()
 for m in entries:
  p=PurePosixPath(m.name);assert not p.is_absolute()and '..'not in p.parts and p.parts[0]==args.case and(m.isdir()or m.isfile())
 for m in entries:
  p=root/m.name
  if m.isdir():p.mkdir(parents=True,exist_ok=True)
  else:
   p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('xb')as out:out.write(archive.extractfile(m).read())
  os.chmod(p,m.mode&0o777)
receipt={'case':args.case,'archive_bytes':len(raw),'archive_sha256':hashlib.sha256(raw).hexdigest(),'local_copy':str(root/args.case),'result':result}
(Path(__file__).resolve().parent/('download-'+args.case+'.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
