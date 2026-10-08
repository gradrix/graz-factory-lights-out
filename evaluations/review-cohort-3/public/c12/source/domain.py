def identity(payload):
 return payload['value']

def feature(p):
 from urllib.parse import unquote_plus
 import re
 def decode(s):
  if re.search(r'%(?![0-9a-fA-F]{2})',s):raise ValueError('escape')
  return unquote_plus(s)
 out=[]
 for f in p['query'].split('&'):
  if not f:continue
  k,sep,v=f.partition('=');out.append([decode(k),decode(v)])
 return out
