def legacy(p):return [e['route'] for e in p['entries']]

def feature(p):
 from collections import defaultdict
 groups=defaultdict(list)
 for e in p['entries']:groups[e['route']].append(e)
 out=[]
 for route,es in sorted(groups.items()):
  n=len(es)
  if n>=p['min_requests']:out.append({'route':route,'requests':n,'errors':sum(e['status']>=500 for e in es),'p95_ms':sorted(e['ms'] for e in es)[(95*n+99)//100-1]})
 return out
