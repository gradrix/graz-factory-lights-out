def legacy(p):
 v=p['document']
 return 'object' if isinstance(v,dict) else 'array' if isinstance(v,list) else 'scalar'

def feature(p):
 names={k.casefold() for k in p['keys']}
 def walk(v):
  if isinstance(v,dict):return {k:p['replacement'] if k.casefold() in names else walk(x) for k,x in v.items()}
  if isinstance(v,list):return [walk(x) for x in v]
  return v
 return walk(p['document'])
