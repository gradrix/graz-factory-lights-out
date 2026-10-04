"""Read-only actual review-trial progress, suitable for SSH stdin."""
import json,time
from pathlib import Path
import sys
stage=Path(sys.argv[1]);root=stage/'trial-1'
launch=json.loads((stage/'trial-1-process.json').read_bytes());process=Path('/proc')/str(launch['pid'])
alive=process.exists()and process.joinpath('stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
rows=[]
for case in sorted(root.glob('case-*')):
 row={'case':case.name};ledger=case/'ledger.json'
 if ledger.exists():
  data=json.loads(ledger.read_bytes());row.update(requests=len(data['requests']),commands=len(data['commands']),remaining_s=round(data['deadline']-time.monotonic(),1),last_request=data['requests'][-1].get('status')if data['requests']else None,phase=data.get('phase'))
 result=case/'result.json'
 if result.exists():
  value=json.loads(result.read_bytes());row.pop('remaining_s',None);row.update(execution_status=value['status'],work_s=value['work_elapsed_s'],cleanup=value.get('cleanup_confirmed'),idle=value.get('idle_confirmed'),decision=value.get('child',{}).get('verdict',{}).get('decision'),error=value.get('child',{}).get('error'))
 else:row['execution_status']='running'if alive else'not_published'
 rows.append(row)
print(json.dumps({'controller_alive':alive,'pid':launch['pid'],'cases':rows,'artifact_manifest_present':(root/'artifact-hashes.json').exists(),'note':'Execution completion and model verdict are not independent correctness.'},indent=2))
