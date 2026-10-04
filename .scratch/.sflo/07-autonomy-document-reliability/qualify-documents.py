#!/usr/bin/env python3
"""Two-phase, root-operated historical-series document qualification; no external retry."""
import argparse,hashlib,json,os,pathlib,subprocess,sys,time
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['acquire','answer'])
 for n in ['repo','candidate','qualification','output']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 for n in ['candidate-sha256','qualification-manifest-sha256','serving-container','expected-serving-id','expected-serving-image']:p.add_argument('--'+n,required=True)
 p.add_argument('--config',type=pathlib.Path);p.add_argument('--gate',type=pathlib.Path);p.add_argument('--gate-sha256');p.add_argument('--run',action='store_true');a=p.parse_args()
 if not a.run:p.error('Explicit coordinator --run required; acquire fetches sources, answer calls model')
 a.repo=a.repo.resolve();a.output=a.output.resolve();a.qualification=a.qualification.resolve();a.candidate=a.candidate.resolve();os.chdir(a.repo);sys.path.insert(0,str(a.repo));os.environ['PYTHONPATH']=str(a.repo)
 def frozen():
  assert sha(a.candidate)==a.candidate_sha256
  for n,h in read(a.candidate)['files'].items():
   path=(a.repo/n).resolve();assert path.is_relative_to(a.repo) and sha(path)==h,n
  assert sha(a.qualification/'manifest.json')==a.qualification_manifest_sha256
  for n,h in read(a.qualification/'manifest.json')['files'].items():assert sha(a.qualification/n)==h,n
 frozen();contract=read(a.qualification/'contract.json');questions=read(a.qualification/'questions.json');assert len(questions)==10 and len({q['name'] for q in questions})==10
 def serving():
  v=json.loads(subprocess.check_output(['docker','inspect',a.serving_container],timeout=15))[0];assert v['State']['Running'] and v['Id']==a.expected_serving_id and v['Image']==a.expected_serving_image
  cmd=v['Config']['Cmd']
  def option(*names):
   for n in names:
    if n in cmd:return cmd[cmd.index(n)+1]
    for item in cmd:
     if n.startswith('--') and item.startswith(n+'='):return item[len(n)+1:]
     if n.startswith('-') and not n.startswith('--') and item.startswith(n) and len(item)>len(n):return item[len(n):]
   raise AssertionError('Missing approved serving option '+names[0])
  facts={'id':v['Id'],'image':v['Image'],'alias':option('--alias'),'context':int(option('-c','--ctx-size')),'cache_k':option('--cache-type-k'),'cache_v':option('--cache-type-v'),'parallel':int(option('-np','--parallel'))}
  assert facts['alias']==contract['profile']['model'] and facts['context']==98304 and facts['cache_k']==facts['cache_v']=='q4_0' and facts['parallel']==1;return facts
 from gflo.documents import DocumentStore,AnswerFailure,answer_request
 identity=serving()
 if a.phase=='acquire':
  assert not a.output.exists(),'Preserve previous acquisition and choose a fresh output'
  a.output.mkdir(parents=True,mode=0o700);store=DocumentStore(a.output/'store');binding={'candidate_sha256':a.candidate_sha256,'qualification_manifest_sha256':a.qualification_manifest_sha256,'serving_before':identity,'sources':{},'status':'acquiring_no_model_calls'};save(a.output/'binding.json',binding)
  for name,source in contract['sources'].items():
   frozen();started=time.monotonic();approval={'url':source['source_url'],'source_version':source['source_version'],'question':'Capture approved source for separately frozen qualification questions.'};save(a.output/(name+'-approval.json'),approval)
   try:
    result=store.acquire(approval);evidence=store.resolve(result['id']);save(a.output/(name+'-evidence.json'),evidence)
    body=evidence['receipt']['body_sha256'];binding['sources'][name]={'status':'acquired','id':result['id'],'body_sha256':body,'evidence_sha256':sha(a.output/(name+'-evidence.json')),'baseline_body_sha256':source['body_sha256'],'body_matches_baseline':body==source['body_sha256'],'elapsed_s':time.monotonic()-started}
   except Exception as error:binding['sources'][name]={'status':'not_attempted_source_failure','error':type(error).__name__+': '+str(error)[:2048],'elapsed_s':time.monotonic()-started}
   save(a.output/'binding.json',binding)
  frozen();binding['serving_after']=serving();assert binding['serving_after']==identity;binding['status']='awaiting_independent_source_alignment' if all(x['status']=='acquired' for x in binding['sources'].values()) else 'source_failure_no_inference';save(a.output/'binding.json',binding);print(binding['status']);return
 assert a.config and a.gate and a.gate_sha256,'Answer requires private config and independently frozen source gate'
 assert sha(a.gate)==a.gate_sha256;gate=read(a.gate);binding=read(a.output/'binding.json')
 assert gate['binding_sha256']==sha(a.output/'binding.json') and gate['qualification_manifest_sha256']==a.qualification_manifest_sha256
 assert gate['decision']=='aligned_for_inference' and gate['reviewer'] and gate['coordinator_go'] is True
 assert set(gate['cases'])=={q['name'] for q in questions} and all(x=='aligned' for x in gate['cases'].values())
 for name,info in binding['sources'].items():
  if not info.get('body_matches_baseline'):
   assert gate.get('changed_source_addenda',{}).get(name),'Changed source needs explicit alignment addendum, not silent rebinding'
 assert binding['candidate_sha256']==a.candidate_sha256 and binding['status']=='awaiting_independent_source_alignment' and identity==binding['serving_after']
 assert not (a.output/'answers').exists(),'Never retry a partially attempted phase';(a.output/'answers').mkdir()
 store=DocumentStore(a.output/'store');evidence_by_source={}
 for name,info in binding['sources'].items():
  assert info['status']=='acquired' and sha(a.output/(name+'-evidence.json'))==info['evidence_sha256'];evidence=store.resolve(info['id']);assert evidence['receipt']==read(a.output/(name+'-evidence.json'))['receipt'];evidence_by_source[name]=evidence
 from gflo.worker import ModelWorker
 config=read(a.config);assert config['model']==contract['profile']['model']
 if config.get('api_key_file'):config['api_key_file']=str((a.config.resolve().parent/config['api_key_file']).resolve())
 client=ModelWorker(config,None);summary={'candidate_sha256':a.candidate_sha256,'binding_sha256':sha(a.output/'binding.json'),'gate_sha256':a.gate_sha256,'rows':[],'status':'running','semantic_verdict':'independent review required'};save(a.output/'answers/summary.json',summary)
 for question in questions:
  frozen();assert serving()==identity;folder=a.output/'answers'/question['name'];folder.mkdir();evidence=evidence_by_source[question['source']]
  # This reconstructs only the public request. It never loads oracle facts into messages.
  request=answer_request(evidence,config['model'],question['question']);assert request['temperature']==0 and request['max_tokens']==2048 and request['reasoning_effort']=='medium' and request['thinking_budget_tokens']==512;save(folder/'initial-request.json',request);started=time.monotonic();row={'name':question['name'],'public_answer_invocations':1}
  try:
   answer=store.answer(evidence['id'],client,question=question['question']);row.update(status='structurally_valid_pending_semantic_review',id=answer['id']);save(folder/'answer.json',answer)
  except AnswerFailure as error:row.update(status='answer_failure',id=error.identifier,error=str(error))
  except Exception as error:row.update(status='operation_error_no_external_retry',error=type(error).__name__+': '+str(error)[:2048])
  row['elapsed_s']=time.monotonic()-started
  if 'id' in row:
   resolved=store.resolve(row['id']);save(folder/'receipt.json',resolved);assert 1<=len(resolved['receipt']['attempts'])<=2;row['attempts']=resolved['receipt']['attempts']
   # Canonical response-1/2.json live in the product store; no fork-local capture counter.
  summary['rows'].append(row);save(a.output/'answers/summary.json',summary)
 frozen();summary['serving_after']=serving();assert summary['serving_after']==identity;summary['status']='complete_pending_independent_semantic_review';save(a.output/'answers/summary.json',summary);print(summary['status'])
if __name__=='__main__':main()
