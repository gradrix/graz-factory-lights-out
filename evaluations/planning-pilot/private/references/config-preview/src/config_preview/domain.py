import copy
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
