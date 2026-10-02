import copy,json,pathlib,sys,threading,urllib.request,urllib.error
from qa_pinned import activate
root=activate('49559e96a6b936a4abb24c7e5558862d1e1ad644');sys.path.insert(0,str(root/'tests'))
import test_runner
from gflo.runner import Factory
from gflo.web import server
from gflo.observe import redact_json
fixture=test_runner.RunnerTests();fixture.setUp()
try:
 f=Factory(fixture.root/'qa-state',lambda *a:{},lambda *a:{'passed':True});rid=f.create(fixture.task);f.resume(rid);artifact=f.state/rid/'attempts/1/worker.json';http=server(f.state,0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{http.server_port}/api/runs/{rid}/artifact?name=attempts/1/worker.json';results=[]
 try:
  for kind,value in [('structured-control',{'password':'ALPHA BETA','count':3,'flag':True}),('quoted-space',{'summary':'password="ALPHA BETA"','count':3,'flag':True}),('quoted-escape',{'summary':'token="ALPHA\\"BETA"','count':3,'flag':True})]:
   original=copy.deepcopy(value);artifact.write_text(json.dumps(value));output=urllib.request.urlopen(url).read().decode();parsed=json.loads(output);assert parsed['count']==3 and parsed['flag'] is True;assert value==original;assert 'ALPHA' not in output
   leaked='BETA' in output;assert leaked==(kind!='structured-control');results.append({'case':kind,'json_valid':True,'secret_suffix_exposed':leaked})
  for kind,contents in [('malformed','{"password":"unterminated'),('oversized',json.dumps({'summary':'x'*(1024*1024)}))]:
   artifact.write_text(contents)
   try:urllib.request.urlopen(url)
   except urllib.error.HTTPError as error:assert error.code==404
   else:raise AssertionError('invalid artifact exposed')
   results.append({'case':kind,'http_status':404})
 finally:http.shutdown();http.server_close();thread.join()
 print(json.dumps(results,indent=2))
 pathlib.Path(__file__).with_suffix('.json').write_text(json.dumps(results,indent=2)+'\n')
finally:fixture.tearDown()
