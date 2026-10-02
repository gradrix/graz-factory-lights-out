import sys,copy,itertools,json,subprocess,random
sys.path.insert(0,'/project with spaces')
from api import dispatch

def check(p,want):
 before=copy.deepcopy(p);r=dispatch(p);assert r==want,(p,r,want);assert p==before
 for row in r:
  assert type(row['spent_cents']) is int and type(row['remaining_cents']) is int and type(row['over_budget']) is bool
 return r

def reject(p):
 before=copy.deepcopy(p)
 try:dispatch(p)
 except ValueError:pass
 else:raise AssertionError(('accepted invalid',p))
 assert p==before
 out=subprocess.run([sys.executable,'/project with spaces/cli.py'],input=json.dumps(p),text=True,capture_output=True,cwd='/tmp',timeout=5)
 assert out.returncode==2 and out.stderr.strip() and not out.stdout and 'Traceback' not in out.stderr

rng=random.Random(730)
for i in range(200):
 limits={k:rng.randrange(1000001) for k in ['Z','a',' 猫 ']};entries=[dict(id=str(n),category=rng.choice(list(limits)),cents=rng.randrange(-1000000,1000001)) for n in range(rng.randrange(201))]
 want=[]
 for k in sorted(limits):
  spent=sum(e['cents'] for e in entries if e['category']==k);want.append(dict(category=k,spent_cents=spent,remaining_cents=limits[k]-spent,over_budget=spent>limits[k]))
 check(dict(action='reconcile',limits=limits,entries=entries),want)
for cents in [-1000000,1000000]:
 spent=200*cents;check(dict(action='reconcile',limits={'x':0},entries=[dict(id=str(i),category='x',cents=cents) for i in range(200)]),[dict(category='x',spent_cents=spent,remaining_cents=-spent,over_budget=spent>0)])
base=dict(action='reconcile',limits={'x':1},entries=[])
invalid=[dict(base,limits=v) for v in [None,[],{'':0},{'x':False},{'x':1.0},{'x':-1},{'x':1000001}]]
invalid += [dict(base,entries=v) for v in [None,{},[None],[[]],[dict(id='x',category='x',cents=-1000001)]]]
entry=dict(id='a',category='x',cents=1)
for key,values in [('id',[None,False,0,'',[]]),('category',[None,False,[],{}]),('cents',[None,False,1.0,'1',-1000001,1000001])]:
 for value in values:invalid.append(dict(base,entries=[entry,dict(entry,id='b',**{key:value})] if key!='id' else [entry,dict(entry,id=value)]))
invalid += [dict(base,entries=[entry,dict(entry)]),dict(base,entries=[entry,dict(id='b',category='x',cents=0,extra=1)]),dict(base,limits={'x':1,'unused':False})]
for p in invalid:reject(p)
assert dispatch({'action':'total','values':[-2,0,3]})==1
print('200 seeded ledgers, 2 extreme aggregate controls,',len(invalid),'invalid API/CLI and atomicity cases PASS')
