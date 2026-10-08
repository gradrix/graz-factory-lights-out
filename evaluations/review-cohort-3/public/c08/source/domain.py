def identity(payload):
 return payload['value']

def feature(p):
 assigned={}
 def visit(i,seen):
  for r in p['choices'][i]:
   if r in seen:continue
   seen.add(r)
   if r not in assigned or visit(assigned[r],seen):assigned[r]=i;return True
  return False
 return sum(visit(i,set()) for i in range(len(p['choices'])))
