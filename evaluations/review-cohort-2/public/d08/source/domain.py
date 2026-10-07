def legacy(p):return len(p['markdown'].splitlines())

def feature(p):
 import re
 fenced=False;used=set();out=[]
 for i,line in enumerate(p['markdown'].splitlines(),1):
  if line.strip().startswith('```'):fenced=not fenced;continue
  if fenced:continue
  m=re.match(r'^(#{1,6}) (.*)$',line)
  if not m:continue
  text=m[2].strip();base=re.sub(r'[^a-z0-9 -]','',text.lower());base=re.sub(r'[ -]+','-',base).strip('-') or 'section'
  anchor=base;n=2
  while anchor in used:anchor=base+'-'+str(n);n+=1
  used.add(anchor);out.append({'level':len(m[1]),'text':text,'line':i,'anchor':anchor})
 return out
