def identity(payload):
 return payload['value']

def feature(p):
 out=[]
 for para in p['text'].split('\n'):
  words=[w for w in para.split(' ') if w];line=''
  for w in words:
   if line and len(line)+1+len(w)>p['width']:out.append(line);line=''
   line=(line+' '+w) if line else w
  out.append(line)
 return out
