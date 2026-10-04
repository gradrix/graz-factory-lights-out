from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1]
def put(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.lstrip('\n'))
def tree(root,files):
 for n,text in files.items():put(root/n,text)
A=ROOT/'cases/manifest-reconcile';B=ROOT/'cases/config-preview'
validation='''import re

def entries(value):
    if not isinstance(value,list) or len(value)>100: raise ValueError('entries')
    result={}
    for item in value:
        if not isinstance(item,dict) or set(item)!={'path','size','sha256'}: raise ValueError('entry')
        path=item['path'];size=item['size'];digest=item['sha256']
        if not isinstance(path,str) or not 1<=len(path)<=120 or any(not re.fullmatch(r'[A-Za-z0-9_.-]+',p) or p in ('.','..') for p in path.split('/')): raise ValueError('path')
        if path in result or type(size)is not int or not 0<=size<=1000000 or not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest): raise ValueError('entry')
        result[path]={'path':path,'size':size,'sha256':digest}
    return result
'''
domain='''from .validation import entries

def compare(before,after):
    left,right=entries(before),entries(after)
    common=left.keys() & right.keys()
    unchanged=sorted(p for p in common if (left[p]['size'],left[p]['sha256'])==(right[p]['size'],right[p]['sha256']))
    modified=[{'path':p,'before_size':left[p]['size'],'after_size':right[p]['size']} for p in sorted(common) if p not in unchanged]
    removed=set(left)-set(right);added=set(right)-set(left);renamed=[]
    signatures={(left[p]['size'],left[p]['sha256'])for p in removed}
    for sig in signatures:
        old=[p for p in removed if (left[p]['size'],left[p]['sha256'])==sig]
        new=[p for p in added if (right[p]['size'],right[p]['sha256'])==sig]
        if len(old)==len(new)==1:renamed.append({'from':old[0],'to':new[0]})
    for item in renamed:removed.remove(item['from']);added.remove(item['to'])
    return {'added':sorted(added),'removed':sorted(removed),'modified':modified,'renamed':sorted(renamed,key=lambda x:x['from']),'unchanged':unchanged}
'''
report='''def totals(before,after):
    old=sum(x['size'] for x in before);new=sum(x['size'] for x in after)
    return {'before_bytes':old,'after_bytes':new,'delta_bytes':new-old}
'''
api='''from .domain import compare
from .report import totals

def run(payload):
    if payload=={'action':'ping'}:return {'ok':True}
    if not isinstance(payload,dict) or set(payload)!={'action','before','after'} or payload['action']!='compare':raise ValueError('payload')
    result=compare(payload['before'],payload['after']);result['summary']=totals(payload['before'],payload['after']);return result
'''
cli='''import json,sys
from .api import run

def main():
    try:result=run(json.load(sys.stdin))
    except (ValueError,TypeError):print(json.dumps({'error':'invalid input'}));return 2
    print(json.dumps(result,sort_keys=True));return 0
'''
afiles={'manifest_tool/__init__.py':'','manifest_tool/validation.py':'def entries(value):\n    raise NotImplementedError("manifest validation")\n','manifest_tool/domain.py':'def compare(before,after):\n    raise NotImplementedError("manifest comparison")\n','manifest_tool/report.py':'def totals(before,after):\n    raise NotImplementedError("manifest summary")\n','manifest_tool/api.py':"def run(payload):\n    if payload=={'action':'ping'}:return {'ok':True}\n    raise ValueError('unknown action')\n",'manifest_tool/cli.py':cli,'main.py':'from manifest_tool.cli import main\nif __name__=="__main__":raise SystemExit(main())\n','README.md':'# Manifest tool\n\nRun `python main.py` with a JSON ping action on standard input.\n'}
tree(A/'source',afiles);tree(ROOT/'private/references/manifest-reconcile',dict(afiles,**{'manifest_tool/validation.py':validation,'manifest_tool/domain.py':domain,'manifest_tool/report.py':report,'manifest_tool/api.py':api,'tests/__init__.py':''}))
errors='''class Conflict(ValueError):
    def __init__(self,index,code):
        self.index=index;self.code=code;super().__init__(code)
'''
bvalidation='''import re
KEY=re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,31}')

def document(value):
    count=0
    def visit(v,depth):
        nonlocal count
        count+=1
        if count>200 or depth>6:raise ValueError('limit')
        if isinstance(v,dict):
            for k,x in v.items():
                if not isinstance(k,str) or not KEY.fullmatch(k):raise ValueError('key')
                visit(x,depth+1)
        elif v is None or type(v)is bool:pass
        elif type(v)is int:
            if not -1000000<=v<=1000000:raise ValueError('integer')
        elif isinstance(v,str):
            if len(v)>80:raise ValueError('string')
        else:raise ValueError('value')
    visit(value,0)

def request(base,operations):
    if not isinstance(base,dict):raise ValueError('base')
    document(base)
    if not isinstance(operations,list) or len(operations)>50:raise ValueError('operations')
    for item in operations:
        if not isinstance(item,dict) or item.get('op') not in ('set','remove','test'):raise ValueError('operation')
        if set(item)!=({'op','path'} if item['op']=='remove' else {'op','path','value'}):raise ValueError('fields')
        path=item['path']
        if not isinstance(path,list) or not 1<=len(path)<=6 or any(not isinstance(k,str) or not KEY.fullmatch(k) for k in path):raise ValueError('path')
        if 'value'in item:document(item['value'])
'''
bdomain='''import copy
from .validation import request,document
from .errors import Conflict
from .audit import event

def same(a,b):
    if type(a)is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(same(a[k],b[k])for k in a)
    return a==b

def preview(base,operations):
    request(base,operations);result=copy.deepcopy(base);audit=[]
    for index,item in enumerate(operations):
        parent=result
        for part in item['path'][:-1]:
            if part not in parent:raise Conflict(index,'parent_missing')
            if not isinstance(parent[part],dict):raise Conflict(index,'parent_not_object')
            parent=parent[part]
        key=item['path'][-1];present=key in parent;before={'present':present,'value':copy.deepcopy(parent.get(key))};op=item['op']
        if op=='test':
            if not present or not same(parent[key],item['value']):raise Conflict(index,'test_failed')
        elif op=='remove':
            if not present:raise Conflict(index,'missing')
            del parent[key]
        else:parent[key]=copy.deepcopy(item['value'])
        try:document(result)
        except ValueError:raise Conflict(index,'limit')
        audit.append(event(index,op,item['path'],before['present'],before['value'],key in parent,parent.get(key)))
    return {'document':result,'audit':audit}
'''
routes='''from fastapi import APIRouter,Body
from fastapi.responses import JSONResponse
from .domain import preview
from .errors import Conflict
router=APIRouter()
@router.post('/config/preview')
def config_preview(payload=Body(...)):
    if not isinstance(payload,dict) or set(payload)!={'base','operations'}:return JSONResponse(status_code=422,content={'error':'invalid input'})
    try:return preview(payload['base'],payload['operations'])
    except Conflict as error:return JSONResponse(status_code=409,content={'error':{'index':error.index,'code':error.code}})
    except ValueError:return JSONResponse(status_code=422,content={'error':'invalid input'})
'''
app='''from fastapi import FastAPI,Body
from fastapi.responses import JSONResponse
from .routes import router
app=FastAPI();app.include_router(router)
@app.get('/health')
def health():return {'status':'ok'}
@app.post('/sum')
def total(payload=Body(...)):
    if not isinstance(payload,dict) or set(payload)!={'values'} or not isinstance(payload['values'],list) or any(type(x)is not int for x in payload['values']):return JSONResponse(status_code=422,content={'error':'invalid input'})
    return {'total':sum(payload['values'])}
'''
pyproject='''[build-system]
requires = ["setuptools==78.1.0"]
build-backend = "setuptools.build_meta"
[project]
name = "gflo-config-preview"
version = "0.0.1"
requires-python = ">=3.12,<3.13"
dependencies = ["fastapi==0.115.12", "uvicorn==0.34.2"]
[tool.setuptools.packages.find]
where = ["src"]
'''
bfiles={'src/config_preview/__init__.py':'','src/config_preview/errors.py':errors,'src/config_preview/validation.py':'def request(base,operations):\n    raise NotImplementedError("configuration validation")\n','src/config_preview/domain.py':'def preview(base,operations):\n    raise NotImplementedError("configuration preview")\n','src/config_preview/routes.py':'from fastapi import APIRouter\nrouter=APIRouter()\n','src/config_preview/app.py':app,'pyproject.toml':pyproject,'README.md':'# Configuration preview\n\nExisting health and integer sum endpoints use config_preview.app:app.\n'}
tree(B/'source',bfiles);tree(ROOT/'private/references/config-preview',dict(bfiles,**{'src/config_preview/validation.py':bvalidation,'src/config_preview/domain.py':bdomain,'src/config_preview/routes.py':routes,'tests/__init__.py':''}))
atests='''import unittest
from manifest_tool.api import run
from manifest_tool.domain import compare
class ManifestTests(unittest.TestCase):
    def test_rename(self):
        a={'path':'old','size':2,'sha256':'a'*64};b=dict(a,path='new')
        self.assertEqual(compare([a],[b])['renamed'],[{'from':'old','to':'new'}])
    def test_ambiguous(self):
        a=lambda p:{'path':p,'size':0,'sha256':'b'*64}
        self.assertEqual(compare([a('x'),a('y')],[a('z')])['renamed'],[])
    def test_bool_rejection(self):
        with self.assertRaises(ValueError):compare([{'path':'x','size':True,'sha256':'a'*64}],[])
'''
btests='''import unittest
from fastapi.testclient import TestClient
from config_preview.app import app
from config_preview.domain import preview
from config_preview.errors import Conflict
class ConfigTests(unittest.TestCase):
    def test_http_set(self):
        r=TestClient(app).post('/config/preview',json={'base':{},'operations':[{'op':'set','path':['x'],'value':3}]})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['document'],{'x':3})
    def test_atomic_conflict(self):
        base={'a':False}
        with self.assertRaises(Conflict):preview(base,[{'op':'set','path':['b'],'value':2},{'op':'test','path':['a'],'value':0}])
        self.assertEqual(base,{'a':False})
    def test_absent_null(self):
        result=preview({},[{'op':'set','path':['x'],'value':None}])
        self.assertEqual(result['audit'][0]['before'],{'present':False,'value':None})
        self.assertEqual(result['audit'][0]['after'],{'present':True,'value':None})
'''
put(ROOT/'private/references/manifest-reconcile/tests/test_manifest.py',atests)
put(ROOT/'private/references/config-preview/tests/test_config.py',btests)
put(ROOT/'private/references/manifest-reconcile/README.md','''# Manifest reconciliation

Compare two file manifests without touching files. Entries carry relative paths, integer sizes and lowercase SHA256 values. Shared paths are classified before unique unmatched signatures become renames; ambiguous signatures remain added and removed paths. Invalid data returns an error without changing inputs.

Run `python /path/to/project/main.py` and send `{"action":"compare","before":[],"after":[]}`. The response is `{"added":[],"removed":[],"modified":[],"renamed":[],"unchanged":[],"summary":{"before_bytes":0,"after_bytes":0,"delta_bytes":0}}`.

Run tests with `python -m unittest discover -s /path/to/project`. Malformed JSON exits2 with `{"error":"invalid input"}`; successful JSON exits0.
''')
put(ROOT/'private/references/config-preview/README.md','''# Configuration preview

This installable package previews ordered nested configuration changes without modifying the request. Set, remove and test operate on explicit key lists. A conflict aborts the preview atomically; missing keys and failed typed tests produce indexed HTTP409 errors. Invalid shapes use HTTP422. Null differs from an absent key; booleans differ from integers.

After offline wheel installation, run `python -m uvicorn config_preview.app:app --host 127.0.0.1 --port 8000`. Send POST `/config/preview` with `{"base":{},"operations":[]}`; response is `{"document":{},"audit":[]}`. GET `/health` remains available. Run tests with `python -m unittest discover -s /path/to/project` using the installed package and approved dependencies.
''')

put(B/'source/src/config_preview/audit.py','def event(index,op,path,before_present,before_value,after_present,after_value):\n    raise NotImplementedError("audit event")\n')
put(ROOT/'private/references/config-preview/src/config_preview/audit.py',"""import copy

def event(index,op,path,before_present,before_value,after_present,after_value):
    return {'index':index,'op':op,'path':list(path),'before':{'present':before_present,'value':copy.deepcopy(before_value) if before_present else None},'after':{'present':after_present,'value':copy.deepcopy(after_value) if after_present else None}}
""")
