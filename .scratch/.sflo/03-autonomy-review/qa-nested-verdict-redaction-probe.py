import json,pathlib,sys,threading,urllib.request
from qa_pinned import activate
root=activate('4346ba5289f24f228f83f6f45646f32e41cd48c1');sys.path.insert(0,str(root/'tests'))
import test_runner
from gflo.runner import Factory
from gflo.web import server
from gflo.observe import redact_json
verdict={'passed':False,'review':{'evidence':'token="ALPHA BETA"'}}
embedded='Previous attempt evidence. Repair the retained files:\n'+json.dumps(verdict)
control=json.loads(redact_json(verdict));actual=json.loads(redact_json({'content':embedded}));assert 'ALPHA BETA' not in json.dumps(control);assert 'ALPHA BETA' in json.dumps(actual)
fixture=test_runner.RunnerTests();fixture.setUp()
try:
 f=Factory(fixture.root/'state-nested',lambda *a:{},lambda *a:{'passed':True});rid=f.create(fixture.task);f.resume(rid);path=f.state/rid/'attempts/1/worker.json';path.write_text(json.dumps({'summary':embedded}));http=server(f.state,0);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
 try:
  text=urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/runs/{rid}/artifact?name=attempts/1/worker.json').read().decode();json.loads(text);assert 'ALPHA BETA' in text
 finally:http.shutdown();http.server_close();thread.join()
finally:fixture.tearDown()
print(json.dumps({'candidate':'4346ba5289f24f228f83f6f45646f32e41cd48c1','structured_control_redacts':True,'embedded_json_secret_retained':True,'http_artifact_same_embedded_string_leaks':True,'outer_json_valid':True,'synthetic_only':True}))
