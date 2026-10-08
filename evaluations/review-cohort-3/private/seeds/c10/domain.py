def identity(payload):
 return payload['value']

def feature(p):
 names=p['candidates'];counts=dict.fromkeys(names,0)
 for ballot in p['ballots']:
  for n in ballot:
   if n not in counts:raise ValueError('unknown candidate')
   counts[n]+=1
 return [{'candidate':n,'votes':counts[n]} for n in sorted(names,key=lambda n:-counts[n])]
