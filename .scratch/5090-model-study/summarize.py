#!/usr/bin/env python3
import json,pathlib,statistics,re
root=pathlib.Path(__file__).parent
def framing_normalized(r):
 if not r.get('expected'):return None
 raw=r.get('text','').strip();m=re.fullmatch(r'```(?:json)?\s*\n(.*?)\n?```',raw,re.S)
 if m:raw=m.group(1)
 try:return json.loads(raw)==r['expected']
 except (ValueError,TypeError):return False
summary=[]
for path in sorted((root/'results').glob('*.jsonl')):
 rows=[json.loads(x) for x in path.read_text().splitlines()]
 speeds=[r['decode_tokens_s'] for r in rows if r['name'] in ('speed_1','speed_2') and r.get('decode_tokens_s')]
 checks=[r for r in rows if 'passed' in r and not r['name'].startswith(('stress_','context_'))]
 contexts=[]
 for r in rows:
  if r['name'].startswith(('stress_','context_')):
   contexts.append({k:r.get(k) for k in ['name','target_context','seed','passed','error','elapsed_s','ttft_s','finish_reason']})
   contexts[-1]['prompt_tokens']=r.get('usage',{}).get('prompt_tokens')
   contexts[-1]['framing_normalized_passed']=framing_normalized(r)
   contexts[-1]['retrieved_all']=r.get('retrieved_all',all(x in r.get('text','') for x in r.get('expected',{}).values()) if r.get('expected') else r.get('passed'))
 summary.append({'label':path.stem,'warm_decode_tps':statistics.mean(speeds) if speeds else None,'warm_decode_range':[min(speeds),max(speeds)] if speeds else None,'checks_passed':sum(bool(r['passed']) for r in checks),'checks_total':len(checks),'failures':[{'name':r['name'],'finish_reason':r.get('finish_reason'),'grade_output':r.get('grade_output')} for r in checks if not r['passed']],'median_answer_s':statistics.median([r['elapsed_s'] for r in checks]) if checks else None,'total_answer_s':sum(r['elapsed_s'] for r in checks),'output_tokens':sum(r.get('usage',{}).get('completion_tokens',0) for r in checks),'contexts':contexts,'errors':[r.get('error') for r in rows if r.get('error')]})
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for r in summary:
 print(r['label'],'speed',round(r['warm_decode_tps'],2) if r['warm_decode_tps'] else '-',f"checks {r['checks_passed']}/{r['checks_total']}")
 for c in r['contexts']:print(' ',c['name'],c['prompt_tokens'],'strict',c['passed'],'retrieved',c['retrieved_all'],'seconds',round(c['elapsed_s'],1) if c['elapsed_s'] else None,c['error'] or '')
