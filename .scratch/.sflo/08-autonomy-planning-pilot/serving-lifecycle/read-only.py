"""Run via ssh stdin on the owned rig; GET and safe Docker inspection only."""
import datetime,json,pathlib,stat,subprocess,time,urllib.request,urllib.error
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('Redirect refused')
def identity():
 v=json.loads(subprocess.check_output(['docker','inspect','gflo-model'],timeout=10))[0]
 cmd=v['Config']['Cmd'];flags={}
 for names in [('--alias',),('-c','--ctx-size'),('-np','--parallel'),('--cache-type-k',),('--cache-type-v',),('--host',),('--port',)]:
  for n in names:
   if n in cmd:flags[names[0]]=cmd[cmd.index(n)+1];break
 return {'id':v['Id'],'image':v['Image'],'running':v['State']['Running'],'started_at':v['State']['StartedAt'],'owner':v['Config'].get('Labels',{}).get('gflo.owner'),'flags':flags,'slots_flag_explicit':'--slots' in cmd,'slots_disabled_explicit':'--no-slots' in cmd,'metrics_flag_explicit':'--metrics' in cmd,'offline':'--offline' in cmd,'ports':v['NetworkSettings']['Ports'],'runtime_entrypoint':v['Config']['Entrypoint']}
p=pathlib.Path.home()/'.local/state/gflo-model/api-key';key=p.read_text().strip()
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
def get(path):
 started=time.monotonic();req=urllib.request.Request('http://127.0.0.1:18000'+path,headers={'Authorization':'Bearer '+key},method='GET')
 try:
  with opener.open(req,timeout=5) as response:
   raw=response.read(65537)
   if len(raw)>65536:raise ValueError('GET body exceeded bound')
   val=json.loads(raw)
   # Never retain token cache, prompts, full configuration, or authentication.
   if path.startswith('/slots') and isinstance(val,list):
    val=[{k:x.get(k) for k in ('id','is_processing','n_ctx','n_tokens','state')} for x in val if isinstance(x,dict)]
   elif path.startswith('/health'):val={k:val.get(k) for k in ('status','slots_idle','slots_processing')} if isinstance(val,dict) else {'unexpected_type':type(val).__name__}
   else:val={'type':type(val).__name__}
   return {'path':path,'http_status':response.status,'safe_body':val,'raw_bytes':len(raw),'elapsed_s':time.monotonic()-started}
 except urllib.error.HTTPError as e:return {'path':path,'http_status':e.code,'elapsed_s':time.monotonic()-started}
 except Exception as e:return {'path':path,'error_type':type(e).__name__,'elapsed_s':time.monotonic()-started}
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operation':'read-only GET; no inference/restart','before':identity(),'key_mode':oct(stat.S_IMODE(p.stat().st_mode)),'samples':[]}
for i in range(2):
 result['samples'].append([get('/health'),get('/slots'),get('/slots?fail_on_no_slot=1')])
 if i==0:time.sleep(1)
result['after']=identity();print(json.dumps(result,indent=2))
