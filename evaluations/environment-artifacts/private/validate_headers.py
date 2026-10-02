"""Read bounded raw TAR headers only. Never extract, follow links, or interpret extensions."""
import hashlib,json,pathlib,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parents[1]

def inspect_raw(data):
 offset=0;rows=[];partial_header=False;partial_body=False;zeros=0
 while offset<len(data):
  block=data[offset:offset+512]
  if len(block)<512:partial_header=True;break
  if block==bytes(512):zeros+=1;offset+=512;continue
  assert zeros==0,'unexpected material after archive terminator'
  recorded=int(block[148:156].strip(b'\x00 ') or b'0',8)
  assert recorded==sum(block[:148])+8*32+sum(block[156:]),'header checksum mismatch'
  size=int(block[124:136].strip(b'\x00 ') or b'0',8)
  name=block[:100].split(b'\x00',1)[0].decode()
  kind=block[156:157].decode();link=block[157:257].split(b'\x00',1)[0].decode()
  mode=oct(int(block[100:108].strip(b'\x00 ') or b'0',8))
  # Slicing is bounded by actual fixture bytes; no allocation based on declared size.
  body=data[offset+512:offset+512+size]
  rows.append({'name':name,'type':kind,'size':size,'link':link,'mode':mode,'available_body_size':len(body),'body_sha256':hashlib.sha256(body).hexdigest()})
  if len(body)<size:partial_body=True;break
  offset+=512+((size+511)//512)*512
 return {'headers':rows,'partial_header':partial_header,'partial_body':partial_body,'zero_blocks':zeros}

def main():
 cases=json.loads((R/'cases.json').read_text());out=[]
 for c in cases:
  data=(R/c['archive']).read_bytes();assert len(data)==c['transport_size'] and hashlib.sha256(data).hexdigest()==c['sha256']
  facts=inspect_raw(data)
  assert len(facts['headers'])==len(c['raw_entries']),c['id']
  for got,want in zip(facts['headers'],c['raw_entries']):
   for k in ['name','type','size','link','mode']:assert got[k]==want[k],(c['id'],k)
   assert got['available_body_size']==want['stored_body_size'],c['id']
   assert got['body_sha256']==want['stored_body_sha256'],c['id']
  if c['id'] in ['21-declared-huge','24-truncated-payload']:assert facts['partial_body']
  elif c['id']=='23-truncated-header':assert facts['partial_header']
  else:assert not facts['partial_header'] and not facts['partial_body'] and facts['zero_blocks']==2
  out.append({'case':c['id'],'header_inventory_matches':True,'facts':facts})
 with tempfile.TemporaryDirectory() as tmp:
  destination=pathlib.Path(tmp)
  subprocess.run(['python3',str(R/'private/generate.py'),'--out',tmp],check=True)
  generated=['cases.json','receipt-publication-scenarios.json','valid-tree-records.json']+[c['archive'] for c in cases]
  for name in generated:assert (destination/name).read_bytes()==(R/name).read_bytes(),('nondeterministic',name)
 report={'validation_scope':'raw byte hashes, checksums, bounded header inventory, intended truncation, deterministic regeneration; no extraction or product acceptance','archive_count':len(cases),'total_archive_bytes':sum(c['transport_size'] for c in cases),'largest_archive_bytes':max(c['transport_size'] for c in cases),'max_declared_file_bytes':max(e['size'] for c in cases for e in c['raw_entries']),'all_inventories_matched':True,'deterministic_regeneration':True,'extract_calls':0,'container_calls':0,'outcomes':out}
 (R/'private/header-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='outcomes'},indent=2))
if __name__=='__main__':main()
