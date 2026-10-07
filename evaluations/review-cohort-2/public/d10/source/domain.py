def legacy(p):return [c['service'] for c in p['checks']]

def feature(p):
 last={c['service']:c for c in p['checks']};up=sum(c['state']=='up' for c in last.values());block={}
 for s in p['required']:
  if s not in last or last[s]['state']!='up':block[s]=1
 for s,c in last.items():
  if c['critical'] and c['state']!='up':block[s]=1
 return {'ready':up>=p['quorum'] and not block,'up':up,'blockers':list(block)}
