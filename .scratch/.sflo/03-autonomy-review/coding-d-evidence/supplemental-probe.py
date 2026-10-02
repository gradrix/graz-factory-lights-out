import sys,copy,json,sqlite3,tempfile,pathlib,hmac,hashlib
sys.path.insert(0,'/workspace')
from api import dispatch
kind=sys.argv[1]
def call(p):
 before=copy.deepcopy(p)
 try:return dispatch(p)
 finally:assert p==before,'input mutation'
def reject(p):
 try:call(p)
 except ValueError:return
 raise AssertionError('expected rejection')
if kind=='01':
 p={'action':'import_contacts','csv':'email,name\n X@Y ," First\nLast "\nx@y,Second\nz@y,Other\n','existing':[{'email':'z@y','name':'old'}]}
 assert call(p)=={'added':[{'email':'x@y','name':'First\nLast'}],'skipped':2}
 for row in ['x@y, ','x@y,Valid,extra']:
  reject({'action':'import_contacts','csv':'email,name\nx@y,First\n'+row+'\n','existing':[]})
elif kind=='04':
 with tempfile.TemporaryDirectory() as td:
  db=str(pathlib.Path(td)/'stock.db');c=sqlite3.connect(db);c.execute('create table stock(sku TEXT PRIMARY KEY,quantity INTEGER NOT NULL)');c.executemany('insert into stock values (?,?)',[('a',2),('b',0)]);c.commit();c.close()
  reject({'action':'adjust','db':db,'changes':[{'sku':'a','delta':-3},{'sku':'a','delta':4}]})
  reject({'action':'adjust','db':db,'changes':[{'sku':'a','delta':3},{'sku':'missing','delta':1}]})
  c=sqlite3.connect(db);assert c.execute('select * from stock order by sku').fetchall()==[('a',2),('b',0)];c.close()
  assert call({'action':'adjust','db':db,'changes':[{'sku':'a','delta':-2},{'sku':'a','delta':1}]})==[{'sku':'a','quantity':1},{'sku':'b','quantity':0}]
  c=sqlite3.connect(db);assert c.execute('select * from stock order by sku').fetchall()==[('a',1),('b',0)];c.close()
  assert {p.name for p in pathlib.Path(td).iterdir()}=={'stock.db'}
elif kind=='07':
 p={'action':'verify','secret':'sëcret','body':'body\n😃','timestamp':2**40,'now':2**40-3600,'tolerance':3600}
 sig='sha256='+hmac.new(p['secret'].encode(),(str(p['timestamp'])+'.'+p['body']).encode(),hashlib.sha256).hexdigest();p['signature']=sig;assert call(p) is True
 for signature in ['',sig+'\n',sig.upper(),'sha256='+'é'*64,'sha256='+'\ud800'*64,sig[:-1]+'g']:
  assert call(dict(p,signature=signature)) is False
 assert call(dict(p,tolerance=3599)) is False
 assert call(dict(p,body=p['body']+'x')) is False
elif kind=='08':
 p={'action':'headings','markdown':'# A\n# A\n# A-2\n# A\n# 😃\n# section\n```x\n# hidden\n ```end\n## Final ###'}
 r=call(p);assert [x['anchor'] for x in r]==['a','a-2','a-2-2','a-3','section','section-2','final'];assert [x['line'] for x in r]==[1,2,3,4,5,6,10]
elif kind=='11':
 p={'action':'redact','document':{'Straße':{'x':1},'keep':[{' PASSWORD ':False,'password':True},[0,None]]},'keys':['STRASSE','PASSWORD'],'replacement':0}
 r=call(p);assert r=={'Straße':0,'keep':[{' PASSWORD ':False,'password':0},[0,None]]};assert type(r['keep'][0][' PASSWORD ']) is bool
 r['keep'][0][' PASSWORD ']=True;r['keep'][1].append('x');assert p['document']['keep']==[{' PASSWORD ':False,'password':True},[0,None]]
else:raise AssertionError(kind)
print('supplemental',kind,'PASS')
