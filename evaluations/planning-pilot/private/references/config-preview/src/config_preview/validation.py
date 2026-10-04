import re
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
