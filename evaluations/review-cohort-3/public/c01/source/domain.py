def identity(payload):
 return payload['value']

def feature(p):
 w=p['weights']; s=p['seats']; t=sum(w)
 if s and not t: raise ValueError('no weight')
 if not s:return [0]*len(w)
 a=[s*x//t for x in w]
 for i in sorted(range(len(w)),key=lambda i:(-(s*w[i]%t),i))[:s-sum(a)]:a[i]+=1
 return a
