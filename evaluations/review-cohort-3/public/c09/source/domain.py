def identity(payload):
 return payload['value']

def feature(p):
 import re
 s=p['text'];parts=re.findall(r'([0-9]+)([hms])',s)
 if not parts or ''.join(a+b for a,b in parts)!=s:raise ValueError('syntax')
 ranks=['hms'.index(u) for n,u in parts]
 if ranks!=sorted(set(ranks)):raise ValueError('unit order')
 return sum(int(n)*{'h':3600,'m':60,'s':1}[u] for n,u in parts)
