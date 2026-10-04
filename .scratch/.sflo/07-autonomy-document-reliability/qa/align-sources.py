"""Independent offline pre-inference binding/oracle source audit."""
import json,hashlib
from pathlib import Path
base=Path('.scratch/.sflo/07-autonomy-document-reliability');acq=base/'rig-acquisition-1';qual=Path('.scratch/autonomy/document-repair-qualification');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();binding=json.loads((acq/'binding.json').read_text());contract=json.loads((qual/'contract.json').read_text());oracle=json.loads((qual/'oracle.json').read_text());manifest=json.loads((qual/'manifest.json').read_text())
assert sha(qual/'manifest.json')==binding['qualification_manifest_sha256']=='0fd8ecff10b17c584e049ae072eb9f31c67f6c33f4dc70beebfbc457e1394de1'
for n,h in manifest['files'].items():assert sha(qual/n)==h
assert binding['candidate_sha256']=='4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e' and binding['serving_before']==binding['serving_after'];evidences={};sources={}
for name,info in binding['sources'].items():
 p=acq/f'{name}-evidence.json';assert sha(p)==info['evidence_sha256'];e=json.loads(p.read_text());rec=e['receipt'];assert e['id']==info['id'];assert rec['body_sha256']==info['body_sha256']==contract['sources'][name]['body_sha256'];assert rec['approval']['url']==contract['sources'][name]['source_url'] and rec['approval']['source_version']==contract['sources'][name]['source_version'];assert rec['extractor']=='document-text-v2'
 old=json.loads(Path(contract['sources'][name]['review_spans_path'] if name=='asyncio' else contract['sources'][name]['path']).read_text());old=old if name=='asyncio' else old['spans'];assert old==e['spans'];evidences[name]=e
 sources[name]={'evidence_id':e['id'],'body_sha256':rec['body_sha256'],'all_spans_equal_baseline':True,'span_count':len(e['spans']),'extractor':rec['extractor'],'retrieved_utc':rec['retrieved_utc']}
rows=[]
for case in oracle:
 e=evidences[case['source']];rows.append({'name':case['name'],'question':case['question'],'expected_status':case['expected_status'],'facts':case['semantic_facts'],'source_passages':{str(i):e['spans'][i-1]for i in case['reference_spans']}})
 # Unsupported-case premise not asserted anywhere in complete supplied sources.
 if case['expected_status']=='insufficient_evidence':assert not any('3.16' in s for s in e['spans'])
(base/'qa/source-alignment-evidence.json').write_text(json.dumps({'sources':sources,'cases':rows},indent=2)+'\n')
gate={'binding_sha256':sha(acq/'binding.json'),'qualification_manifest_sha256':binding['qualification_manifest_sha256'],'decision':'aligned_for_inference','reviewer':'independent qa_resume','coordinator_go':False,'cases':{case['name']:'aligned' for case in oracle},'changed_source_addenda':{},'source_alignment_report':'qa-source-alignment.md'};(base/'source-alignment-gate.json').write_text(json.dumps(gate,indent=2)+'\n');print('gate_sha256',sha(base/'source-alignment-gate.json'));print('binding_sha256',sha(acq/'binding.json'))
