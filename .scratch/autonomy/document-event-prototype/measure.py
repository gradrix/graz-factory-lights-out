"""Disposable measurement wrapper; only event limit changes between trials."""
import hashlib,json,pathlib,resource,sys,time
import document_extract as module
module.EVENT_LIMIT=int(sys.argv[1]);instances=[]
class Measured(module.Extractor):
 def __init__(self):super().__init__();self.max_depth=0;instances.append(self)
 def handle_starttag(self,tag,attrs):
  try:return super().handle_starttag(tag,attrs)
  finally:self.max_depth=max(self.max_depth,len(self.stack))
module.Extractor=Measured
body=pathlib.Path('/body').read_bytes();started=time.perf_counter();cpu=time.process_time();spans=None;error=None
try:spans=module.extract(body,'text/html')
except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
wall=time.perf_counter()-started;cpu=time.process_time()-cpu;parser=instances[0] if instances else None
print(json.dumps({'event_limit':module.EVENT_LIMIT,'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'status':'passed' if error is None else 'rejected','error':error,'events':parser.events if parser else None,'max_depth':parser.max_depth if parser else None,'raw_visible_text_bytes':parser.bytes if parser else None,'spans':len(spans) if spans is not None else None,'partial_spans':len(parser.spans) if parser else None,'text_bytes':sum(len(s.encode()) for s in spans) if spans is not None else None,'spans_sha256':hashlib.sha256(json.dumps(spans,ensure_ascii=True,separators=(',',':')).encode()).hexdigest() if spans is not None else None,'extract_wall_s':wall,'extract_cpu_s':cpu,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'python':sys.version.split()[0]}))
