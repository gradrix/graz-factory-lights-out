import pathlib,sys,json,tempfile
sys.path.insert(0,str(pathlib.Path.cwd()))
from gflo.documents import DocumentStore
from gflo.recipes.document import frame
from gflo import guard
out=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(tempfile.mkdtemp(prefix='gflo-doc-bounds-'));body=b'';kind='text/plain';rows=[];app={'url':'https://docs.python.org/3.12/library/json.html','source_version':'synthetic bounds','question':'fixture'}
def executor(args,name,timeout,**kw):
 if args[-1]!='fetch':return guard.run(args,name,timeout,**kw)
 meta={'url':app['url'],'status':200,'content_type':kind,'charset':'utf-8','cache_control':'public','connected':'1.1.1.1','body_size':len(body),'http_headers':{'content-type':kind,'cache-control':'public','content-length':str(len(body))}};kw['output'].write(frame(meta,body));pathlib.Path(kw['inspect_path']).write_text('{"QA":"in-memory fetch"}');return {'exit_code':0,'output':''}
store=DocumentStore(root/'store',executor=executor)
for label,kind,body,want in [('text-at','text/plain',b'x'*131072,True),('text-over','text/plain',b'x'*131073,False),('depth-at','text/html',b'<div>'*64+b'x'+b'</div>'*64,True),('depth-over','text/html',b'<div>'*65+b'x'+b'</div>'*65,False),('blocks-at','text/plain',b'x\n'*2048,True),('blocks-over','text/plain',b'x\n'*2049,False),('events-at','text/html',b'<!--x-->'*9997+b'<p>x</p>',True),('events-over','text/html',b'<!--x-->'*9998+b'<p>x</p>',False)]:
 before=set(store.root.iterdir())
 try:r=store.acquire(app)
 except ValueError as e:assert not want,(label,str(e));assert set(store.root.iterdir())==before;rows.append({'case':label,'reject':str(e)})
 else:assert want;rows.append({'case':label,'passed':True,'id':r['id']})
 (out/'bounds-results.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS8pairedactualofflineextractionbounds')
