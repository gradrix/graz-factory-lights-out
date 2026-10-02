import hashlib,io,json,pathlib,sys,tempfile,shutil,tarfile,socket
from unittest.mock import patch,Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('25f75c3275739cc7cc2a4fc5a4e16580b81511d1')
import gflo.prepare as prep
from gflo.environment import EnvironmentStore
from gflo.recipes import fetch as client
OUT=pathlib.Path(__file__).resolve().parent;ROOT=pathlib.Path(tempfile.mkdtemp(prefix='gflo-input-qa-'));rows=[]
def save():(OUT/'results.json').write_text(json.dumps({'candidate':'25f75c3275739cc7cc2a4fc5a4e16580b81511d1','root':str(ROOT),'results':rows},indent=2)+'\n')
spec={'filename':'x.whl','url':'https://files.pythonhosted.org/packages/x.whl','algorithm':'sha256','digest':hashlib.sha256(b'good').hexdigest(),'max_bytes':4}
class Response(io.BytesIO):
 def __init__(self,data,status=200,headers=None):super().__init__(data);self.status=status;self.headers=headers or {};self.reads=0
 def getheader(self,n):return self.headers.get(n)
 def read(self,n):self.reads+=1;return super().read(n)
for label,body,status,headers,error in [('control',b'good',200,{'Content-Length':'4'},None),('non200',b'',503,{},'non-200'),('redirect',b'',302,{'Location':'https://elsewhere/x'},'non-200'),('truncated',b'goo',200,{'Content-Length':'4'},'incomplete'),('declared-cap',b'',200,{'Content-Length':'5'},'declared'),('actual-cap',b'good!',200,{},'actual'),('hash',b'evil',200,{},'hash')]:
 response=Response(body,status,headers);connection=Mock();connection.getresponse.return_value=response
 with patch.object(client,'resolve',return_value=['1.1.1.1']),patch.object(client,'Connection',return_value=connection):
  try:actual=client.fetch(spec)
  except ValueError as e:assert error and error in str(e)
  else:assert error is None and actual==b'good'
 assert connection.close.call_count==1
 if label in ['non200','redirect','declared-cap']:assert response.reads==0
 rows.append({'case':'fetch-'+label,'passed':True,'reads':response.reads});save()
with patch.object(client.socket,'getaddrinfo',side_effect=socket.timeout('QA DNS timeout')),patch.object(client,'Connection') as connection:
 try:client.fetch(spec)
 except socket.timeout:pass
 else:raise AssertionError('DNS timeout accepted')
 connection.assert_not_called()
rows.append({'case':'DNS-timeout-propagates-before-connection','passed':True})
raw=Mock();raw.connect.side_effect=socket.timeout('QA connect timeout')
with patch.object(client.socket,'socket',return_value=raw):
 connection=client.Connection('files.pythonhosted.org','1.1.1.1')
 try:connection.connect()
 except socket.timeout:pass
 else:raise AssertionError('connect timeout accepted')
 raw.close.assert_called_once();raw.settimeout.assert_called_once_with(10)
rows.append({'case':'numeric-connect-timeout-closes-socket','passed':True});save()
# Replace only online acquisition with a tar stream from independently frozen local wheels.
recipes=ROOT/'recipes';shutil.copytree(prep.RECIPES,recipes);prep.RECIPES=recipes;wheels=pathlib.Path('.gflo/environment-locks/python-api/wheels').resolve();real_execute=prep.execute;mode='control';acquired=[]
def execute(image,command,work,**kwargs):
 if not kwargs.get('online'):return real_execute(image,command,work,**kwargs)
 specs=json.loads((kwargs['approved']/'artifacts.json').read_text());acquired.clear()
 with tarfile.open(fileobj=kwargs['output'],mode='w|',format=tarfile.USTAR_FORMAT) as archive:
  for i,s in enumerate(specs):
   data=(wheels/s['filename']).read_bytes();assert hashlib.new(s['algorithm'],data).hexdigest()==s['digest'];acquired.append(s['filename'])
   if i==0 and mode=='missing':continue
   if i==0 and mode=='corrupt':data=b'corrupt'
   h=tarfile.TarInfo(s['filename']);h.size=len(data);h.mode=0o444;archive.addfile(h,io.BytesIO(data))
 return {'exit_code':0},{'QA':'frozen local artifact stream; no network'}
prep.execute=execute;store=EnvironmentStore(ROOT/'store');good=prep.prepare(store,'python-api');rows.append({'case':'local-locked-control-real-offline-assembly','passed':True,'id':good.id,'artifacts':len(acquired)});save()
def inventory():return {str(p.relative_to(store.root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob('*') if p.is_file() and not any(s.startswith('.') for s in p.relative_to(store.root).parts)}
before=inventory();lock=recipes/'python-api/requirements.lock';original=lock.read_text()
for mode in ['missing','corrupt','lock-mismatch']:
 if mode=='lock-mismatch':lock.write_text(original.replace('sha256:f', 'sha256:0',1))
 try:prep.prepare(store,'python-api')
 except ValueError as e:message=str(e)
 else:raise AssertionError(mode+' accepted')
 finally:lock.write_text(original)
 assert inventory()==before;assert store.resolve(good.id).receipt_hash==good.receipt_hash
 rows.append({'case':'prepare-'+mode,'passed':True,'error':message[-2500:],'prior_good_unchanged':True});save()
print('PASS fetch controls/failures and missing/corrupt/lock mismatch without publication')
