"""Final publication and public CLI controls."""
import io,json,pathlib,tempfile
from unittest.mock import patch
import probe
d=probe.d;rows=[]
for mode in ['success-no-postcommit-io','failure-no-postcommit-io']:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  store,evidence,client,answer=probe.fixture(pathlib.Path(td));committed=[False];attempted=[]
  rename=pathlib.Path.rename;read=d.checked_file;write=d.write_file;remove=d.shutil.rmtree;replay=store._replay
  def moved(path,target):result=rename(path,target);committed[0]=True;return result
  def wrap(name,fn):
   def invoke(*args,**kw):
    if committed[0]:attempted.append(name);raise AssertionError('Postcommit '+name)
    return fn(*args,**kw)
   return invoke
  error=None;value=None
  with patch.object(d,'bounded_answer',return_value=probe.response(answer if mode.startswith('success') else '{bad')),patch.object(pathlib.Path,'rename',moved),patch.object(d,'checked_file',wrap('read',read)),patch.object(d,'write_file',wrap('write',write)),patch.object(d.shutil,'rmtree',wrap('cleanup',remove)),patch.object(store,'_replay',wrap('render',replay)):
   try:value=store.answer(evidence['id'],client)
   except d.AnswerFailure as e:error=e
  assert committed[0] and not attempted
  assert (value is not None)==mode.startswith('success')
  identifier=value['id'] if value else error.identifier;assert store.resolve(identifier)['id']==identifier
  rows.append({'case':mode,'committed':True,'postcommit_operations':attempted,'kind':store.resolve(identifier)['receipt']['kind']})
with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
 root=pathlib.Path(td);store,evidence,client,answer=probe.fixture(root);config=root/'config.json';config.write_text(json.dumps({'model':'local','endpoint':'http://127.0.0.1:1'}))
 from gflo.__main__ import main
 with patch.object(d,'bounded_answer',return_value=probe.response('{bad')) as calls,patch('sys.stdout',new_callable=io.StringIO) as stdout,patch('sys.stderr',new_callable=io.StringIO) as stderr:
  code=main(['--config',str(config),'documents','--store',str(store.root),'answer',evidence['id']])
 new=probe.ids(store)-{evidence['id']};assert len(new)==1;identifier=new.pop()
 assert code==1 and identifier in stderr.getvalue() and not stdout.getvalue() and calls.call_count==2
 rows.append({'case':'failure-cli','exit':code,'stderr':stderr.getvalue(),'stdout':stdout.getvalue(),'calls':calls.call_count,'kind':store.resolve(identifier)['receipt']['kind']})
with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
 store,evidence,client,answer=probe.fixture(pathlib.Path(td));calls=[]
 with patch.object(d,'bounded_answer',side_effect=lambda *a,**k:calls.append(True)):
  try:store.answer('0'*64,client)
  except OSError:pass
  else:raise AssertionError('Unavailable source admitted')
 assert not calls;rows.append({'case':'unavailable-source','calls':0,'refused':True})
(probe.OUT/'final-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
