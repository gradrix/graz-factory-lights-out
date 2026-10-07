def legacy(p):return sorted(p['variables'])

def feature(p):
 import re
 s=p['template'];out=[];i=0
 while i<len(s):
  if s[i]!='$':out.append(s[i]);i+=1;continue
  if s[i:i+2]=='$$':out.append('$');i+=2;continue
  if s[i:i+2]!='${':raise ValueError('dollar')
  end=s.find('}',i+2)
  if end<0:raise ValueError('brace')
  name=s[i+2:end]
  if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name) is None or name not in p['variables']:raise ValueError('variable')
  out.append(p['variables'][name]);i=end+1
 return ''.join(out)
