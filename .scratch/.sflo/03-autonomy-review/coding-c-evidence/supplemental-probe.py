import sys,itertools,copy
sys.path.insert(0,'/workspace')
from api import dispatch
kind=sys.argv[1]
def call(p):
 before=copy.deepcopy(p)
 try:return dispatch(p)
 finally:assert p==before,'input mutation'
if kind=='01':
 for n in range(5):
  for ws in itertools.product(range(4),repeat=n):
   for seats in range(8):
    p=dict(action='allocate',weights=list(ws),seats=seats)
    if not sum(ws) and seats:
     try:call(p)
     except ValueError:continue
     raise AssertionError('zero-total rejection absent')
    if not sum(ws):expected=[0]*n
    else:
     qr=[divmod(w*seats,sum(ws)) for w in ws];expected=[q for q,r in qr]
     for i in sorted(range(n),key=lambda i:(-qr[i][1],i))[:seats-sum(expected)]:expected[i]+=1
    assert call(p)==expected,(p,expected)
elif kind=='08':
 options=[list(x for i,x in enumerate('abc') if mask & (1<<i)) for mask in range(8)]
 for choices in itertools.product(options,repeat=3):
  expected=max(sum(v is not None for v in assignment) for assignment in itertools.product(*[[None]+x for x in choices]) if len([v for v in assignment if v is not None])==len(set(v for v in assignment if v is not None)))
  assert call(dict(action='match',choices=[x+x for x in choices]))==expected,choices
elif kind=='12':
 good={'a=%2526&b=%26&c=%2B+d':[['a','%26'],['b','&'],['c','+ d']],'&&=x&&a=b=c&empty&':[['','x'],['a','b=c'],['empty','']],'nul=%00&unicode=%F0%9F%98%80':[['nul','\x00'],['unicode','😀']]}
 for q,expected in good.items():assert call(dict(action='parse',query=q))==expected
 for q in ['a=%','a=%0','a=%GG','a=%C0%80','a=%ED%A0%80','a=%F4%90%80%80','a=%80','a=%E2%82']:
  try:call(dict(action='parse',query=q))
  except ValueError:continue
  raise AssertionError(q)
else:raise AssertionError(kind)
print('supplemental',kind,'PASS')
