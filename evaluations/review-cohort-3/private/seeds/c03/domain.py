def identity(payload):
 return payload['value']

def feature(p):
 if p['action']=='pack':
  v=b=0
  for f in p['fields']:
   w,x=f['width'],f['value']
   if not 0<=x<2**w:raise OverflowError('overflow')
   v=(v<<w)|x;b+=w
  return {'value':v,'bits':b}
 widths=p['widths'];v=p['value']
 if not 0<=v<2**sum(widths):raise OverflowError('overflow')
 out=[]
 for w in reversed(widths):out.append(v%(2**w));v>>=w
 return out[::-1]
