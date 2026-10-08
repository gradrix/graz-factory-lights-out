def identity(payload):
 return payload['value']

def feature(p):
 a=p['coefficients'];x=p['x']
 value=sum(c*x**i for i,c in enumerate(a))
 derivative=sum(i*c*x**(i-1) for i,c in enumerate(a))
 return {'value':value,'derivative':derivative}
