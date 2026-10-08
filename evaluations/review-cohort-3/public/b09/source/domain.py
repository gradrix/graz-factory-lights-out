def revision(payload):
    return payload['document']['revision']

from copy import deepcopy

def migrate(payload):
    out=deepcopy(payload['document']);rev=out['revision']
    if rev==3:return out
    if rev not in (1,2):raise ValueError('revision')
    users=out.pop('users');accounts={};order=[]
    for user in users:
        key=user['id']
        if key in accounts:raise ValueError('duplicate id')
        order.append(key)
        accounts[key]={'profile':{'name':user['name']},'enabled':user['active']} if rev==1 else {'profile':user['profile'],'enabled':user['enabled']}
    out.update(revision=3,accounts=accounts,order=order)
    return out
