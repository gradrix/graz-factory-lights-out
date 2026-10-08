def identity(payload):
 return payload['value']

def feature(p):
 s=p['number'].replace(' ','').replace('-','')
 def valid(s):
  total=0
  for i,c in enumerate(reversed(s)):
   v=int(c)*(2 if i%2 else 1);total+=v-9 if v>9 else v
  return total%10==0
 if p['action']=='check':return bool(s) and valid(s)
 if not s:raise ValueError('empty')
 return next(s+str(i) for i in range(10) if valid(s+str(i)))
