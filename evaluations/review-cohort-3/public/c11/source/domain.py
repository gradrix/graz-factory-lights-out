def identity(payload):
 return payload['value']

def feature(p):
 if p['action']=='encode':
  out=[]
  for v in p['values']:
   if out and out[-1][0]==v:out[-1][1]+=1
   else:out.append([v,1])
  return out
 if any(n<=0 for v,n in p['runs']) or sum(n for v,n in p['runs'])>10000:raise ValueError('size')
 return [v for v,n in p['runs'] for _ in range(n)]
