def identity(payload):
 return payload['value']

def feature(p):
 from collections import deque
 g=p['grid'];s=tuple(p['start']);e=tuple(p['end'])
 if g[s[0]][s[1]]=='#' or g[e[0]][e[1]]=='#':return None
 q=deque([(s,0)]);seen={s}
 while q:
  (r,c),d=q.popleft()
  if (r,c)==e:return d
  for x,y in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
   if 0<=x<len(g) and 0<=y<len(g[0]) and g[x][y]=='.' and (x,y) not in seen:seen.add((x,y));q.append(((x,y),d+1))
 return None
