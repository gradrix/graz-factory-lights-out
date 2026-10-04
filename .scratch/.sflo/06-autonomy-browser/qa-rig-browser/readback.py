"""Read-only rig evidence validation; run via ssh python3 -; no imports of runtime."""
import hashlib,json,pathlib,struct
root=pathlib.Path('/home/gradrix/gflo-browser-596ecb6');out=root/'.gflo/rig-qualification-v5';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=root/'.scratch/.sflo/06-autonomy-browser/builder-candidate-v5.json';assert sha(manifest)=='ee60bbe4012e03acbcd5a9cd403a63f62290dd253c97a7f7979ead062ee53ea4'
for n,h in json.loads(manifest.read_text())['files'].items():assert sha(root/n)==h,n
fixture=root/'evaluations/local-browser';assert sha(fixture/'manifest.json')=='20d07c59c1af28f5728847179406560787b579b86c20c030e30032492f16ac10'
for n,h in json.loads((fixture/'manifest.json').read_text())['files'].items():assert sha(fixture/n)==h,n
rows=[]
for path in sorted((out/'five-flows').glob('*-receipt.json')):
 result=json.loads(path.read_text());rec=result['receipt'];saved=out/'five-flows/store'/result['id'];assert sha(saved/'receipt.json')==result['id'];assert json.loads((saved/'receipt.json').read_text())==rec
 for n,info in rec['artifacts'].items():
  artifact=saved/'artifacts'/n;assert sha(artifact)==info['sha256'] and artifact.stat().st_size==info['size']
  if n.endswith('.png'):assert struct.unpack('>II',artifact.read_bytes()[16:24])==(1280,800)
 positive='-control-' in path.name;assert (rec['outcome']['status']=='passed')==positive
 if not positive:assert rec['outcome']['failure']['phase']=='journey'
 assert rec['executor']['facts']['cleanup']['confirmed'] is True
 containers=rec['executor']['facts']['containers'];assert len(containers)==2
 for name,fact in containers.items():
  host=fact['host'];assert host['Runtime']=='runc' and host['ReadonlyRootfs'] and host['LogConfig']['Type']=='none';assert fact['config']['User']=='1000:1000'
  assert host['Memory']==host['MemorySwap'];assert host['NetworkMode']=='none' if 'browser-app-' in name else host['NetworkMode'].startswith('container:')
 rt=rec['outcome'].get('runtime',{});row={'case':path.stem,'id':result['id'],'status':rec['outcome']['status'],'cleanup':True,'artifacts_verified':len(rec['artifacts'])}
 if positive:
  assert rt['shm']['peakBytes']>0 and rt['shm']['samples']>0;assert len(rt['network']['denials'])==4 and all(not x['connected'] for x in rt['network']['denials'])
  renderers=[x for x in rt['isolation']['processes'] if '--type=renderer' in x['command']];assert renderers
  for renderer in renderers:assert renderer['namespaces']['user']!=rt['isolation']['reporter']['user'] and '--no-sandbox' not in renderer['command'] and '--disable-dev-shm-usage' not in renderer['command']
  row.update(shm=rt['shm'],versions={k:rt[k] for k in ['node','playwright','core','browser']},contexts=len(rt['traces']))
 rows.append(row)
assert len(rows)==10
print(json.dumps({'source_fixture_hashes_match':True,'rows':rows},indent=2))
