from copy import deepcopy

def read(payload):
    return deepcopy(payload['records'].get(payload['id']))

def update(payload):
    records=deepcopy(payload['records']);key=payload['id'];expected=payload['expected'];old=records.get(key)
    applied=(old is None and expected is None) or (old is not None and expected is not None and old['version']==expected)
    if applied:
        data={} if old is None else deepcopy(old['data'])
        data.update(deepcopy(payload['patch']))
        records[key]={'version':1 if old is None else old['version']+1,'data':data}
    return {'applied':applied,'records':records,'record':deepcopy(records.get(key))}
